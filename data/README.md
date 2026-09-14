# Data inputs

Large raw MaleCNS connectome files are intentionally not stored in this repository.

The final research notebook used public MaleCNS connectivity and annotation tables, including a connectivity file named:

```text
connectome-weights-male-cns-v1.0-minconf-0.5.feather
```

A corresponding MaleCNS neuron-annotation table is also required to reconstruct the 532-neuron navigation-related subset and family metadata.

## Expected local layout

```text
data/
└─ raw/
   ├─ connectome-weights-male-cns-v1.0-minconf-0.5.feather
   └─ <MaleCNS neuron annotation table>
```

The exact annotation filename may depend on the version downloaded from the public source.

## Why raw data are excluded

Raw connectome files are excluded from GitHub because they are substantially larger than the compact generated outputs needed to inspect the final project. The repository instead stores code, documentation, result figures, manifests, and the compact frozen controller artifact.

## Final circuit derived from the inputs

The released controller contains:

- 532 neurons
- 5,274 recurrent edges after thresholding
- 36 PFL2/PFL3 motor-readout neurons

The included `docs/modeling_conventions.md` file describes the modeling assumptions used when converting the public connectome into the recurrent controller.
