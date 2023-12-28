using System;
using System.IO;
using System.Text;
using UnityEngine;

namespace Lbsm
{
    [System.Serializable]
    public struct LbsmAxes
    {
        public string x;
        public string y;
        public string z;

        public static readonly LbsmAxes Unity = new LbsmAxes
        {
            x = "left",
            y = "up",
            z = "forward",
        };

        public static readonly LbsmAxes Gltf = new LbsmAxes
        {
            x = "left",
            y = "up",
            z = "forward",
        };

        public static readonly LbsmAxes OpenGL = new LbsmAxes
        {
            x = "right",
            y = "up",
            z = "back",
        };

        public override string ToString()
        {
            return $"[{x}-{y}-{z}]";
        }
    }

    [System.Serializable]
    public struct LbsmCoordinates
    {
        public LbsmAxes axes;
        public string uvOrigin;

        public static readonly LbsmCoordinates Unity = new LbsmCoordinates
        {
            axes = LbsmAxes.Unity,
            uvOrigin = "lowerLeft",
        };

        public static readonly LbsmCoordinates Gltf = new LbsmCoordinates
        {
            axes = LbsmAxes.Gltf,
            uvOrigin = "upperLeft",
        };

        public static readonly LbsmCoordinates OpenGL = new LbsmCoordinates
        {
            axes = LbsmAxes.OpenGL,
            uvOrigin = "lowerLeft",
        };

        public override string ToString()
        {
            return $"{{{axes}; {uvOrigin}}}";
        }
    }

    [System.Serializable]
    public class LbsmAsset
    {
        public string version;
        public LbsmCoordinates coordinates;
        public override string ToString()
        {
            return $"{{version: {version}}}";
        }
    }

    [System.Serializable]
    public class LbsmBufferView
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
    public class LbsmAttribute
    {
        public string vertexAttribute;
        public string format;
        public int dimension;
    }

    [System.Serializable]
    public class LbsmStream
    {
        public int bufferView;
        public LbsmAttribute[] attributes;
    }

    [System.Serializable]
    public class LbsmIndices
    {
        public int stride;
        public int bufferView;
    }

    [System.Serializable]
    public class LbsmSubMesh
    {
        public int material;
        public int drawCount;
    }

    [System.Serializable]
    public struct LbsmMorphTarget
    {
        public string name;
        public int indexStride;
        public int indexBufferView;
        public int positionBufferView;
        public LbsmMorphTarget(string name, int indexStride, int indexBufferView, int positionBufferView)
        {
            this.name = name;
            this.indexStride = indexStride;
            this.indexBufferView = indexBufferView;
            this.positionBufferView = positionBufferView;
        }
    }

    [System.Serializable]
    public class LbsmMesh
    {
        public string name;
        public int vertexCount;
        public LbsmStream[] vertexStreams;
        public LbsmIndices indices;
        public LbsmSubMesh[] subMeshes;
        public int[] joints;
        public LbsmMorphTarget[] morphTargets;
        public override string ToString()
        {
            return $"{{name: {name}, vertexStreams: {vertexStreams}, indices: {indices}, joints: {joints}}}";
        }
    }

    [System.Serializable]
    public class LbsmBone
    {
        public string name;
        public int parent;
        public float[] head;
        public float[] tail;
        bool is_connected;
        public override string ToString()
        {
            return $"{name}({head[0]}, {head[1]}, {head[2]})";
        }
    }

    [System.Serializable]
    public class LbsmTexture
    {
        public int bufferView;
    }

    [System.Serializable]
    public class LbsmMaterial
    {
        public string name;
        public float[] color;
        public int colorTexture;
    }

    [System.Serializable]
    public class LbsmRoot
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

        public LbsmAsset asset;
        public LbsmBufferView[] bufferViews;
        public LbsmTexture[] textures;
        public LbsmMaterial[] materials;
        public LbsmMesh[] meshes;
        public LbsmBone[] bones;

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