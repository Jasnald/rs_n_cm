import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # mesmo não usado diretamente, ativa 3D

# 1) Carrega o JSON
path = r"T:\02_SHK\05_dgl_gm\08_Project\Modules_Post_ED2\Sample_postprocess\Choosed_plane\Sample1__2_rebuild_from_curve.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2) Extrai a lista de dicionários
pts_dicts = data["points"]

# 3) Constrói listas (ou array) de x, y, z
xs = [p["x"] for p in pts_dicts]
ys = [p["y"] for p in pts_dicts]
# pode escolher 'z_original' ou 'z_fitted'. Aqui usamos z_fitted:
zs = [p["z_fitted"] for p in pts_dicts]

# 4) Opcionalmente monte um array Nx3
pts = np.vstack([xs, ys, zs]).T   # shape (N,3)

# 5) Plota
fig = plt.figure(figsize=(8,6))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(pts[:,0], pts[:,1], pts[:,2], s=1, c=pts[:,2], cmap="viridis")
ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_zlabel("Z fitted (mm)")
plt.title("Nuvem de pontos reconstruída")
plt.tight_layout()
plt.show()