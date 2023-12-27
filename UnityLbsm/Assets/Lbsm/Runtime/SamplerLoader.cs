using System;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using System.Collections.Generic;
using Lbsm;
using Unity.VisualScripting;
using UnityEngine.Assertions.Must;


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

    static readonly Lbsm.LbsmAxes UnityAxes = new Lbsm.LbsmAxes
    {
        x = "right",
        y = "up",
        z = "forward",
    };
    static readonly Lbsm.LbsmAxes GltfAxes = new Lbsm.LbsmAxes
    {
        x = "left",
        y = "up",
        z = "forward",
    };
    static readonly Lbsm.LbsmAxes OpenGLAxes = new Lbsm.LbsmAxes
    {
        x = "right",
        y = "up",
        z = "back",
    };

    static void load(GameObject go, byte[] data)
    {
        if (Lbsm.LbsmRoot.TryParse(data, out var json, out var bin))
        {
            Debug.Log(json);
            var lbsm = JsonUtility.FromJson<Lbsm.LbsmRoot>(json);
            Debug.Log(lbsm);

            var bones = new Transform[lbsm.bones.Length];
            for (int i = 0; i < lbsm.bones.Length; ++i)
            {
                var bone = new GameObject(lbsm.bones[i].name).transform;
                bones[i] = bone;
                bone.SetParent(go.transform);
                var position = lbsm.bones[i].head;
                bone.localPosition = new Vector3(
                    position[0],
                    position[1],
                    position[2]
                );
                if (lbsm.asset.axes.Equals(UnityAxes))
                {
                }
                else if (lbsm.asset.axes.Equals(GltfAxes))
                {
                    bone.localPosition = bone.localPosition.ReverseX();
                }
                else if (lbsm.asset.axes.Equals(OpenGLAxes))
                {
                    bone.localPosition = bone.localPosition.ReverseZ();
                }
                else
                {
                    throw new ArgumentException($"invalid axes: {lbsm.asset.axes}");
                }
            }
            for (int i = 0; i < lbsm.bones.Length; ++i)
            {
                if (lbsm.bones[i].parent != -1)
                {
                    bones[i].SetParent(bones[lbsm.bones[i].parent], true);
                }
            }

            var textures = lbsm.textures.Select(src =>
            {
                var texture = new Texture2D(2, 2);
                var buffer = lbsm.bufferViews.First(x => x.name == src.bufferView);
                if (texture.LoadImage(bin.Slice(buffer.byteOffset, buffer.byteLength).ToArray()))
                {
                    return texture;
                }
                return null;
            }).ToArray();

            var materials = lbsm.materials.Select(x =>
            {
                var material = new Material(Shader.Find("Standard"));
                material.name = x.name;
                if (x.colorTexture != -1)
                {
                    material.mainTexture = textures[x.colorTexture];
                }
                return material;
            }).ToArray();
            foreach (var src in lbsm.meshes)
            {
                var mesh = loadMesh(go, lbsm, bin, src);
                var meshOb = new GameObject(src.name);
                meshOb.transform.SetParent(go.transform);

                if (src.joints?.Length > 0)
                {
                    var bindposes = new Matrix4x4[src.joints.Length];
                    for (int i = 0; i < src.joints.Length; ++i)
                    {
                        var joint = bones[src.joints[i]];
                        bindposes[i] = new Matrix4x4(
                            new Vector4(1, 0, 0, 0),
                            new Vector4(0, 1, 0, 0),
                            new Vector4(0, 0, 1, 0),
                            new Vector4(-joint.position.x, -joint.position.y, -joint.position.z, 1)
                        );
                    }
                    mesh.bindposes = bindposes;

                    var renderer = meshOb.AddComponent<SkinnedMeshRenderer>();
                    renderer.sharedMesh = mesh;
                    renderer.bones = bones;
                    renderer.sharedMaterial = new Material(Shader.Find("Standard"));
                    renderer.sharedMaterials = src.subMeshes.Select(x => materials[x.material]).ToArray();
                }
                else
                {
                    var filter = meshOb.AddComponent<MeshFilter>();
                    filter.sharedMesh = mesh;
                    var renderer = meshOb.AddComponent<MeshRenderer>();
                    renderer.sharedMaterial = new Material(Shader.Find("Standard"));
                    renderer.sharedMaterials = src.subMeshes.Select(x => materials[x.material]).ToArray();
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

    static IEnumerable<int> FlipTriangles(int[] indices)
    {
        for (int i = 0; i < indices.Length; i += 3)
        {
            yield return indices[i + 2];
            yield return indices[i + 1];
            yield return indices[i];
        }
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
        var materias = new Material[] { };
        var ib = lbsm.bufferViews.First(x => x.name == src.indices.bufferView);
        var indexCount = ib.byteLength / src.indices.stride;
        mesh.SetIndexBufferParams(indexCount, src.indices.stride == 2 ? IndexFormat.UInt16 : IndexFormat.UInt32);
        mesh.SetIndexBufferData(bin.Array, bin.Offset + ib.byteOffset, 0, ib.byteLength);
        mesh.subMeshCount = src.subMeshes.Length;
        var offset = 0;
        for (int i = 0; i < src.subMeshes.Length; ++i)
        {
            mesh.SetSubMesh(i, new SubMeshDescriptor
            {
                indexStart = offset,
                indexCount = src.subMeshes[i].drawCount,
            });
            offset += src.subMeshes[i].drawCount;
        }

        if (lbsm.asset.axes.Equals(UnityAxes))
        {
        }
        else if (lbsm.asset.axes.Equals(GltfAxes))
        {
            mesh.vertices = mesh.vertices.Select(x => x.ReverseX()).ToArray();
            mesh.normals = mesh.normals.Select(x => x.ReverseX()).ToArray();
            // right handed
            mesh.triangles = FlipTriangles(mesh.triangles).ToArray();
        }
        else if (lbsm.asset.axes.Equals(OpenGLAxes))
        {
            mesh.vertices = mesh.vertices.Select(x => x.ReverseZ()).ToArray();
            mesh.normals = mesh.normals.Select(x => x.ReverseZ()).ToArray();
            // right handed
            mesh.triangles = FlipTriangles(mesh.triangles).ToArray();
        }
        else
        {
            throw new NotImplementedException($"invalid axes: {lbsm.asset.axes}");
        }

        mesh.RecalculateBounds();
        return mesh;
    }
}

static class Vector3Extensions
{
    public static Vector3 ReverseX(this Vector3 v)
    {
        return new Vector3(-v.x, v.y, v.z);
    }

    public static Vector3 ReverseZ(this Vector3 v)
    {
        return new Vector3(v.x, v.y, -v.z);
    }
}