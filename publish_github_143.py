"""Release automatisieren; Voraussetzung: lokaler WINDOWS-Build und 'gh auth login'.

GitHub version.json wird erst nach einem verifizierten Release-Asset geändert.
Der bewährte KBM-Updater selbst bleibt unberührt.
"""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

REPO = 'svenherdes/KBM-Trainer-Updates'
VERSION = '1.4.3'
TAG = 'v' + VERSION
ROOT = Path(__file__).resolve().parent
SETUP = ROOT / 'dist' / 'installer' / f'KBM-Trainer-Setup-{VERSION}.exe'


def gh(*args):
    p = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        raise RuntimeError('GitHub-Kommando fehlgeschlagen: ' + ' '.join(args[:4])+'\n'+(p.stderr or p.stdout).strip())
    return p.stdout


def api_json(path):
    return json.loads(gh('api', path))


def main():
    if sys.platform != 'win32':
        raise RuntimeError('Dieses Skript ist nur fuer die Windows-Version vorgesehen.')
    if not SETUP.is_file() or SETUP.stat().st_size < 1_000_000:
        raise RuntimeError('Windows-Setup fehlt oder ist unplausibel klein: ' + str(SETUP))
    if not shutil.which('gh'):
        raise RuntimeError('GitHub CLI fehlt. Installiere sie mit: winget install --id GitHub.cli -e')
    gh('auth', 'status')
    account = api_json('user').get('login')
    if account != 'svenherdes':
        raise RuntimeError('Falsches GitHub-Konto angemeldet: '+str(account)+'. Erwartet: svenherdes.')
    manifest_file = ROOT / 'dist' / 'installer' / 'version.json'
    if not manifest_file.exists():
        raise RuntimeError('Release-Manifest wurde noch nicht erstellt. Build zuerst ausfuehren.')
    desired = json.loads(manifest_file.read_text(encoding='utf-8'))
    sha = hashlib.sha256(SETUP.read_bytes()).hexdigest()
    assert desired['version']==VERSION
    assert desired['sha256'].lower()==sha
    assert desired['download_url'].endswith('/releases/download/'+TAG+'/'+SETUP.name)

    remote = api_json(f'repos/{REPO}/contents/version.json')
    manifest_before = json.loads(base64.b64decode(remote['content']).decode('utf-8'))
    old_version = manifest_before.get('version', '')
    if old_version not in ('1.4.2', '1.4.3'):
        raise RuntimeError('GitHub steht unerwartet auf Version '+str(old_version)+'; kein automatisches Ueberschreiben.')
    if old_version == VERSION:
        if manifest_before['sha256'].lower()==sha:
            print('Die identische Version 1.4.3 ist bereits veroeffentlicht.')
            return
        raise RuntimeError('Version 1.4.3 steht schon mit anderer Pruefsumme online. Abbruch.')

    # Der Update-Dialog darf erst freigeschaltet werden, wenn das Setup abrufbar ist.
    try:
        rel = api_json(f'repos/{REPO}/releases/tags/{TAG}')
    except RuntimeError:
        rel = None
    if rel is None:
        print('Lade Windows-Setup als GitHub-Release hoch ...')
        gh('release','create',TAG,str(SETUP),'--repo',REPO,'--title',
           f'KBM Trainer {VERSION}','--notes',desired['notes'],'--latest')
    rel=api_json(f'repos/{REPO}/releases/tags/{TAG}')
    matching=[a for a in rel.get('assets',[]) if a.get('name')==SETUP.name and a.get('state')=='uploaded']
    if len(matching)!=1:
        raise RuntimeError('Windows-Setup ist im Release nicht nachgewiesen. version.json bleibt unveraendert.')
    asset=matching[0]
    if asset.get('size')!=SETUP.stat().st_size:
        raise RuntimeError('Release-Assetgroesse ist abweichend. version.json bleibt unveraendert.')
    digest=asset.get('digest')
    if not digest or digest.lower()!='sha256:'+sha:
        raise RuntimeError('GitHub bestaetigt den SHA-256 des Setups nicht. version.json bleibt unveraendert.')
    if asset['browser_download_url']!=desired['download_url']:
        raise RuntimeError('Download-Adresse stimmt nicht ueberein. version.json bleibt unveraendert.')

    print('Setup samt SHA-256 verifiziert. Schalte Updatehinweis frei ...')
    payload=base64.b64encode((json.dumps(desired,ensure_ascii=False,indent=2)+'\n').encode('utf-8')).decode('ascii')
    data=json.loads(gh('api','--method','PUT',f'repos/{REPO}/contents/version.json',
                      '-f',f'message=KBM Trainer {VERSION}: Neues Windows-Update freigeben',
                      '-f',f'content={payload}','-f',f'sha={remote["sha"]}','-f','branch=main'))
    assert data.get('commit',{}).get('sha')
    print('ERFOLG: GitHub version.json ist jetzt '+VERSION+'. Der alte Trainer erkennt das Update beim Start, sofern die automatische Pruefung aktiviert ist.')

if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print('\nVEROEFFENTLICHUNG NICHT ABGESCHLOSSEN:',error,file=sys.stderr)
        sys.exit(1)
