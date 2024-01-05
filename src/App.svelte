<script lang="ts">
  import GlView from "./GlView.svelte";
  import Humanoid from "./Humanoid.svelte";
  import * as THREE from "three";

  function createScene(): THREE.Scene {
    const scene = new THREE.Scene();

    // grid
    const size = 10;
    const divisions = 10;
    const gridHelper = new THREE.GridHelper(size, divisions);
    scene.add(gridHelper);

    // cube
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.MeshPhongMaterial({
      color: "#fff", // オブジェクト白
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = Math.PI * 0.15; // x軸の回転角(ラジアン)
    mesh.rotation.y = Math.PI * 0.25; // y軸の回転角(ラジアン)

    // light
    const light = new THREE.PointLight();
    light.position.x = 0.5;
    light.position.y = 0.5;
    light.position.z = 3.5;
    scene.add(mesh);
    scene.add(light);

    return scene;
  }

  function createCamera(): THREE.PerspectiveCamera {
    const fov = 45;
    const aspect = 1;
    const camera = new THREE.PerspectiveCamera(fov, aspect, 1, 1000);
    camera.position.z = 3;
    return camera;
  }
</script>

<GlView scene={createScene()} camera={createCamera()} />
<Humanoid />
