## Comparisons testbed (Gin / Hydra / pconfigs)

This directory exists to keep the comparison docs runnable and correct:

- `../gin.md`
- `../hydra.md`
- `../pconfigs.md`

It contains small, standalone implementations of the “tiny trainer” example for:

- **Gin**: `gin/`
- **Hydra / OmegaConf**: `hydra/`
- **pconfigs**: tested against `project/` in this testbed directory (a tiny internal package used only for docs verification)

### Run

```bash
bash run.sh
```

