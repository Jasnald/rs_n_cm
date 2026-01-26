import os, glob, json, numpy as np, matplotlib.pyplot as plt
import inspect, sys
sys.path.append(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))

from set_dir import _set_dir
current_dir, root_dir = _set_dir()                       # ← já definido no seu projeto
curves_dir = os.path.join(current_dir, "Sample_postprocess", "Choosed_curve")

xs = np.linspace(0, 40, 200)

def y(params, x):
    return sum(a * x**i for i, a in enumerate(params))

lines = []
for fp in glob.glob(os.path.join(curves_dir, "*.json")):
    with open(fp) as f:
        data = json.load(f)
    ys = [y(data["params"], x) for x in xs]
    line, = plt.plot(xs, ys, label=os.path.splitext(os.path.basename(fp))[0])
    lines.append(line)

if lines:
    plt.legend()
else:
    print("Nenhum JSON encontrado em", curves_dir)

plt.xlabel("x")
plt.ylabel("z")
plt.tight_layout()
plt.show()