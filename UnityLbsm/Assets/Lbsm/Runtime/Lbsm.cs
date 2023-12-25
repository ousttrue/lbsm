using System;
using System.Text;

namespace Lbsm
{

    [System.Serializable]
    public class Asset
    {
        public string version;
        public override string ToString()
        {
            return $"{{version: {version}}}";
        }
    }

    [System.Serializable]
    public class BufferView
    {
        public string name;
        public int byteOffset;
        public int byteLength;
        public override string ToString()
        {
            return $"{{name: {name}, byteOffset: {byteOffset}, byteLength: {byteLength}}}";
        }
    }

    [System.Serializable]
    public class Mesh
    {
        public string name;
        public string vertices;
        public string indices;
        public override string ToString()
        {
            return $"{{name: {name}, vertices: {vertices}, indices: {indices}}}";
        }
    }

    [System.Serializable]
    public class Lbsm
    {
        public static readonly byte[] MAGIC = new ASCIIEncoding().GetBytes("LBSM");
        public static string ParseChunkType(Span<byte> bytes)
        {
            var end = 0;
            for (; end < bytes.Length; ++end)
            {
                if (bytes[end] == 0)
                {
                    break;
                }
            }
            return new ASCIIEncoding().GetString(bytes.Slice(0, end));
        }

        public Asset asset;
        public BufferView[] bufferViews;
        public Mesh[] meshes;

        public override string ToString()
        {
            var sb = new StringBuilder();

            sb.AppendLine("{");
            sb.AppendLine($"  asset: {asset},");
            sb.AppendLine("  bufferViews:[");

            foreach (var b in bufferViews)
            {
                sb.Append("    ");
                sb.Append(b);
                sb.AppendLine(",");
            }
            sb.AppendLine("  ],");
            sb.AppendLine("  meshes: [");
            foreach (var m in meshes)
            {
                sb.Append("    ");
                sb.Append(m);
                sb.AppendLine(",");
            }
            sb.AppendLine("  ]");
            sb.AppendLine("}");
            return sb.ToString();
        }

        public static bool TryParse(byte[] bytes, out string json, out ArraySegment<byte> bin)
        {
            var reader = new BinaryReader(bytes);

            json = default;
            bin = default;
            if (!reader.ReadBytes(4).AsSpan().SequenceEqual(MAGIC))
            {
                // throw new ArgumentException("invalid magic");
                return false;
            }
            var version = reader.ReadInt();
            // Debug.Log($"version: {version}");

            var length = reader.ReadInt();

            while (reader.Position < length)
            {
                var chunkSize = reader.ReadInt();
                var chunkType = ParseChunkType(reader.ReadBytes(4));
                var chunk = reader.ReadBytes(chunkSize);
                // Debug.Log($"chunk: {chunkType}: {chunkSize} bytes");
                switch (chunkType)
                {
                    case "JSON":
                        json = new System.Text.UTF8Encoding(false).GetString(chunk);
                        break;

                    case "BIN":
                        bin = chunk;
                        break;
                }
            }

            return true;
        }
    }
}