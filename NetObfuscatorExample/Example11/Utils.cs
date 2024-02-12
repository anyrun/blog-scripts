using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Example11
{
    internal class Utils
    {
        public static readonly Random random = new Random();        

        private const int HieroglyphStart = 0x13000;
        private const int HieroglyphEnd = 0x14000;

        public static string GetRandStr(int min = 7, int max = 15)
        {
            
            var l = random.Next(min, max + 1);
            var s = new StringBuilder(l);
            for (int i = 0; i < l; i++)
            {
                var charCode = random.Next(HieroglyphStart, HieroglyphEnd + 1);
                var hieroglyph = char.ConvertFromUtf32(charCode);
                s.Append(hieroglyph);
            }
            return s.ToString();
        }
        public static void Shuffle(int[] keyId)
        {
            for (int i = keyId.Length - 1; i > 0; i--)
            {
                int j = random.Next(i + 1);
                int temp = keyId[i];
                keyId[i] = keyId[j];
                keyId[j] = temp;
            }
        }
    }
}
