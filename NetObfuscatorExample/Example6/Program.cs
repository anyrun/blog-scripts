using System;

namespace Example6
{
    internal class Program
    {
        static void Main(string[] args)
        {
            int ch;
            string secretCode = "";            

            ch = 'c';
            secretCode += ((char)ch).ToString();
            ch = 'o';
            secretCode += ((char)ch).ToString();
            ch = 'd';
            secretCode += ((char)ch).ToString();
            ch = 'e';
            secretCode += ((char)ch).ToString();

            Console.WriteLine(secretCode);            
        }
    }
}
