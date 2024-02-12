using System;

namespace Example10
{
    internal class Program
    {
        static void Main(string[] args)
        {
            string secretCode = "";
            int num = 2;

            while (true)
            {
                switch (num)
                {
                    case 0:
                        secretCode += "d";
                        num = 3;
                        break;
                    case 1:
                        Console.WriteLine(secretCode);
                        num = 5;
                        break;
                    case 2:
                        secretCode += "c";
                        num = 4;
                        break;
                    case 3:
                        secretCode += "e";
                        num = 1;
                        break;
                    case 4:
                        secretCode += "o";
                        num = 0;
                        break;
                    default:
                        goto LabelExit;                        
                }
            }
            LabelExit:;
        }
    }
}
