using System;

namespace Example5
{
    internal class Program
    {
        public const string src = "c:\\Source\\ObfDiveP1\\Build\\Example1.exe";
        public const string dst = "c:\\Source\\ObfDiveP1\\Build\\Example1_obf.exe";

        public const string className = "Example1.Program";
        public const string methodName = "ProtectMe";

        static void Main(string[] args)
        {
            try
            {
                // create obfuscator
                var obfuscator = new SimpleObfuscator(src, dst);

                // obfuscate function "ProtectMe"
                obfuscator.Obfuscate(className, methodName);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ERROR] {ex.Message}");
            }
        }
    }
}
