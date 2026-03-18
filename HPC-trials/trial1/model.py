import numpy as np

# Tiny dataset: y = 2x + 1 with noise
np.random.seed(42)
X = np.random.rand(100, 1)
y = 2 * X.squeeze() + 1 + np.random.randn(100) * 0.1

# Manual linear regression (no sklearn needed)
X_b = np.c_[np.ones((100, 1)), X]          # add bias term
theta = np.linalg.lstsq(X_b, y, rcond=None)[0]

print("=== Linear Regression Results ===")
print(f"Intercept : {theta[0]:.4f}  (true: 1.0)")
print(f"Slope     : {theta[1]:.4f}  (true: 2.0)")

pred = X_b @ theta
mse = np.mean((pred - y) ** 2)
print(f"MSE       : {mse:.6f}")
print("Done.")
