using System;
using System.Text;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEditor;
using UnityEngine.Assertions.Must;
using Unity.Collections;
using Unity.VisualScripting;
using Palmmedia.ReportGenerator.Core.Reporting.Builders;
using System.Collections.Generic;

public class SampleLoader : MonoBehaviour
{
    [SerializeField]
    TextAsset _asset;

    // Start is called before the first frame update
    void Start()
    {
        Byte[] data = default;
        if (_asset != null)
        {
            data = _asset.bytes;
        }
        else
        {
            data = System.IO.File.ReadAllBytes("../tmp.lbsm");
        }
        load(gameObject, data);
    }

    static void load(GameObject go, byte[] data)
    {
        if (Lbsm.LbsmRoot.TryParse(data, out var json, out var bin))
        {
            Debug.Log(json);
            var lbsm = JsonUtility.FromJson<Lbsm.LbsmRoot>(json);
            Debug.Log(lbsm);

            foreach (var src in lbsm.meshes)
            {
                var mesh = loadMesh(go, lbsm, bin, src);
                var meshOb = new GameObject(src.name);
                meshOb.transform.SetParent(go.transform);

                if (src.joints?.Length > 0)
                {
                    var bindposes = new Matrix4x4[src.joints.Length];
                    var bones = new Transform[src.joints.Length];
                    for (int i = 0; i < src.joints.Length; ++i)
                    {
                        bones[i] = new GameObject(src.joints[i].name).transform;
                        bones[i].SetParent(go.transform);
                        bindposes[i] = Matrix4x4.identity;
                    }
                    mesh.bindposes = bindposes;

                    var renderer = meshOb.AddComponent<SkinnedMeshRenderer>();
                    renderer.sharedMesh = mesh;
                    renderer.bones = bones;
                    renderer.sharedMaterial = new Material(Shader.Find("Standard"));
                }
                else
                {
                    var filter = meshOb.AddComponent<MeshFilter>();
                    filter.sharedMesh = mesh;
                    var renderer = meshOb.AddComponent<MeshRenderer>();
                    renderer.sharedMaterial = new Material(Shader.Find("Standard"));
                }
            }
        }
    }

    static VertexAttribute GetAttribute(string attr)
    {
        switch (attr)
        {
            // 0
            case "position":
                return VertexAttribute.Position;
            case "normal":
                return VertexAttribute.Normal;
            case "tangent":
                return VertexAttribute.Tangent;
            // 1
            case "color":
                return VertexAttribute.Color;
            case "tex0":
                return VertexAttribute.TexCoord0;
            case "tex1":
                return VertexAttribute.TexCoord1;
            // 2
            case "blendWeights":
                return VertexAttribute.BlendWeight;
            case "blendIndices":
                return VertexAttribute.BlendIndices;
        }
        throw new ArgumentException(attr);
    }

    static VertexAttributeFormat GetFormat(string format)
    {
        switch (format)
        {
            case "f32":
                return VertexAttributeFormat.Float32;
            case "u16":
                return VertexAttributeFormat.UInt16;
            case "u32":
                return VertexAttributeFormat.UInt32;
        }
        throw new ArgumentException(format);
    }

    static Mesh loadMesh(GameObject go, Lbsm.LbsmRoot lbsm, ArraySegment<byte> bin, Lbsm.LbsmMesh src)
    {
        var layout = new List<VertexAttributeDescriptor>();
        for (int stream = 0; stream < src.vertexStreams.Length; ++stream)
        {
            foreach (var attr in src.vertexStreams[stream].attributes)
            {
                layout.Add(new VertexAttributeDescriptor(
                    GetAttribute(attr.vertexAttribute),
                    GetFormat(attr.format),
                    attr.dimension,
                    stream));
            }
        }

        var mesh = new Mesh();
        mesh.SetVertexBufferParams(src.vertexCount, layout.ToArray());
        for (int stream = 0; stream < src.vertexStreams.Length; ++stream)
        {
            var buffer = lbsm.bufferViews.First(x => x.name == src.vertexStreams[stream].bufferView);
            mesh.SetVertexBufferData(bin.Array, bin.Offset + buffer.byteOffset, 0, buffer.byteLength, stream);
        }

        // index
        var ib = lbsm.bufferViews.First(x => x.name == src.indices.bufferView);
        var indexCount = ib.byteLength / src.indices.stride;
        mesh.SetIndexBufferParams(indexCount, src.indices.stride == 2 ? IndexFormat.UInt16 : IndexFormat.UInt32);
        mesh.SetIndexBufferData(bin.Array, bin.Offset + ib.byteOffset, 0, ib.byteLength);
        mesh.SetSubMesh(0, new SubMeshDescriptor
        {
            indexCount = indexCount,
        });

        mesh.RecalculateBounds();
        return mesh;
    }
}
