using Windows.Services.Store;

static int Finish(string status)
{
    Console.WriteLine(status);
    return 0;
}

try
{
    if (args.Length != 1 || (args[0] != "check" && args[0] != "install"))
        return Finish("UNAVAILABLE");

    // StoreContext benoetigt eine korrekt installierte Microsoft-Store-Paketidentitaet.
    // Auf einem portablen Testbuild nicht ausfuehren.
    var context = StoreContext.GetDefault();
    var updates = await context.GetAppAndOptionalStorePackageUpdatesAsync();
    if (updates.Count == 0)
        return Finish("NONE");

    if (args[0] == "check")
        return Finish("AVAILABLE");

    var status = await context.RequestDownloadAndInstallStorePackageUpdatesAsync(updates);
    return status.OverallState == StorePackageUpdateState.Completed
        ? Finish("INSTALLED")
        : Finish("ERROR");
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message);
    return Finish("ERROR");
}
