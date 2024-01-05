<script lang="ts">
  import { onMount } from "svelte";
  import { ThreeApp } from "./ThreeApp";
  import * as THREE from "three";

  export let scene: THREE.Scene;
  export let camera: THREE.PerspectiveCamera;

  let el: HTMLCanvasElement;
  let wrap: HTMLDivElement;
  let app: ThreeApp;
  let observer: ResizeObserver;

  // https://svelte.jp/tutorial/onmount
  onMount(async () => {
    app = new ThreeApp(el, scene, camera);
    app.animate();

    // wrap size to canvas
    observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        if (entry.contentBoxSize) {
          // Firefox は `contentBoxSize` を配列ではなく、単一のコンテンツ矩形として実装しています。
          const contentBoxSize: ResizeObserverSize = Array.isArray(
            entry.contentBoxSize,
          )
            ? entry.contentBoxSize[0]
            : entry.contentBoxSize;
          app.resize(contentBoxSize.inlineSize, contentBoxSize.blockSize);
        } else {
          app.resize(entry.contentRect.width, entry.contentRect.height);
        }
      }

      console.log("Size changed", entries);
    });
    observer.observe(wrap);
  });
</script>

<div style="width:100%;height:50%;background:black;" bind:this={wrap}>
  <canvas bind:this={el}></canvas>
</div>
