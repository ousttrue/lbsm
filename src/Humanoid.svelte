<script lang="ts">
  import { Pane, Slider, List } from "svelte-tweakpane-ui";

  let innerWidth = 0;
  let width = 800;
  let height = 800;
  let rows = 5;
  let columns = 5;
  let size = 128;
  let sizeOptions = {
    "64px": 64,
    "128px": 128,
    "256px": 256,
    "512px": 512,
    "1024px": 1024,
  };

</script>

<Pane title="Flex" position="fixed">
  <Slider bind:value={width} label="Window Width" min={450} max={800} />
  <Slider bind:value={height} label="Window Height" min={450} max={800} />
  <Slider bind:value={rows} label="Rows" step={1} min={3} max={8} />
  <Slider bind:value={columns} label="Columns" step={1} min={3} max={8} />
  <List bind:value={size} label="MatCap Size" options={sizeOptions} />
</Pane>

<ul>
  <li>leftShoulder</li>
  <li>leftUpperArm</li>
  <li>leftLowerArm</li>
  <li>leftHand</li>
</ul>

<ul>
  <li>head</li>
  <li>neck</li>
  <li>uppserChest</li>
  <li>chest</li>
  <li>spine</li>
  <li>hips</li>
</ul>

<ul>
  <li>leftUpperLeg</li>
  <li>leftLowerLeg</li>
  <li>leftFoot</li>
  <li>leftToes</li>
</ul>
