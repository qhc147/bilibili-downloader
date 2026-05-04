using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;

class Launcher
{
    static void Main()
    {
        string dir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        ProcessStartInfo psi = new ProcessStartInfo
        {
            FileName = Path.Combine(dir, "python", "pythonw.exe"),
            Arguments = "\"" + Path.Combine(dir, "src", "main.py") + "\"",
            WorkingDirectory = dir,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        Process.Start(psi);
    }
}
