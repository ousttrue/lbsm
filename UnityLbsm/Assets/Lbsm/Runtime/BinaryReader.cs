using System;

namespace Lbsm
{
    public class BinaryReader
    {
        byte[] _data;
        int _pos;
        public int Position => _pos;

        public BinaryReader(byte[] data)
        {
            _data = data;
        }

        public ArraySegment<byte> ReadBytes(int length)
        {
            var span = new ArraySegment<byte>(_data, _pos, length);
            _pos += length;
            return span;
        }

        public int ReadInt()
        {
            var span = ReadBytes(4);
            return BitConverter.ToInt32(span);
        }
    }
}