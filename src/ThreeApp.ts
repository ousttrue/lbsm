import * as THREE from 'three';
import { OrbitControls } from "three/addons/controls/OrbitControls.js";


export class ThreeApp {
  renderer: THREE.WebGLRenderer;
  orbit: OrbitControls;

  constructor(
    public readonly canvas: HTMLCanvasElement,
    public readonly scene: THREE.Scene,
    public readonly camera: THREE.PerspectiveCamera,
  ) {
    this.orbit = new OrbitControls(camera, canvas);
    this.orbit.mouseButtons = {
      LEFT: THREE.MOUSE.DOLLY,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.ROTATE,
    }

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true
    });
    // this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setClearColor('#000'); // 背景黒
    this.applyElementSize();
  }

  applyElementSize() {
    this.resize(this.canvas.width, this.canvas.height);
  }

  resize(_w: number, _h: number) {
    const w = Math.ceil(_w);
    const h = Math.ceil(_h);
    // console.log(w, h);
    // swapchain
    this.canvas.width = w;
    this.canvas.height = h;
    this.renderer.setSize(w, h);
    // projection
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.applyElementSize();
    this.orbit.update();
    this.renderer.render(this.scene, this.camera);
  }
}
