using System;
using System.Text;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

public class SampleLoader : MonoBehaviour
{
    [SerializeField]
    TextAsset _asset;

    // Start is called before the first frame update
    void Start()
    {
        if (Lbsm.Lbsm.TryParse(_asset.bytes, out var json, out var bin))
        {
            Debug.Log(json);
            var lbsm = JsonUtility.FromJson<Lbsm.Lbsm>(json);
            Debug.Log(lbsm);

            var mesh = new Mesh();

            var vb = lbsm.bufferViews.First(x => x.name == lbsm.meshes[0].vertices);
            var stride = 8 * 4;// pos3, nom3, uv2
            var layout = new[]
            {
                new VertexAttributeDescriptor(VertexAttribute.Position, VertexAttributeFormat.Float32, 3),
                new VertexAttributeDescriptor(VertexAttribute.Normal, VertexAttributeFormat.Float32, 3),
                new VertexAttributeDescriptor(VertexAttribute.TexCoord0, VertexAttributeFormat.Float32, 2),
            };
            var vertexCount = vb.byteLength / stride;
            mesh.SetVertexBufferParams(vertexCount, layout);
            mesh.SetVertexBufferData(bin.Array, bin.Offset + vb.byteOffset, 0, vb.byteLength);

            var ib = lbsm.bufferViews.First(x => x.name == lbsm.meshes[0].indices);
            var indexCount = ib.byteLength / 2;
            mesh.SetIndexBufferParams(indexCount, IndexFormat.UInt16);
            mesh.SetIndexBufferData(bin.Array, bin.Offset + ib.byteOffset, 0, ib.byteLength);
            Debug.Log(vb);

            mesh.SetSubMesh(0, new SubMeshDescriptor
            {
                indexCount = indexCount,
            });

            var filter = gameObject.AddComponent<MeshFilter>();
            filter.sharedMesh = mesh;
            var renderer = gameObject.AddComponent<MeshRenderer>();
            renderer.sharedMaterial = new Material(Shader.Find("Standard"));
        }
    }
}
