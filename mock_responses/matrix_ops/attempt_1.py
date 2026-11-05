"""matrix_ops.py - converted from matrix_ops.m

Linear algebra and MATLAB indexing conventions (1-based, column-major, end).
"""
import numpy as np

A = np.array([[4, -2, 1], [-2, 4, -2], [1, -2, 4]], dtype=float)  # symmetric positive definite
b = np.array([11, -16, 17], dtype=float)

x = np.linalg.solve(A, b)                  # MATLAB: A \ b (mldivide) -> np.linalg.solve
detA = np.linalg.det(A)                    # MATLAB: det -> np.linalg.det
Ainv = np.linalg.inv(A)                    # MATLAB: inv -> np.linalg.inv
ev = np.sort(np.linalg.eigvalsh(A))        # MATLAB: sort(eig(A)) -> np.sort(np.linalg.eigvalsh)
residual = np.linalg.norm(A @ x - b)       # MATLAB: norm -> np.linalg.norm

B = np.arange(1, 13).reshape(3, 4)    # MATLAB: reshape -> np.reshape
B_flat = B.flatten(order="F")              # MATLAB: B(:)' -> flatten(order='F')
sub = B[1:3][:, [0, -1]]                   # MATLAB: B(2:3, [1 end]) -> B[1:3][:, [0, -1]]
K = np.kron(np.eye(2), np.array([[1, 2], [3, 4]]))  # MATLAB: kron, eye -> np.kron, np.eye

C = A * A.T + 2                            # MATLAB: A .* A' -> A * A.T (elementwise)
D = A @ A.T                                # MATLAB: A * A' -> A @ A.T (matrix product)
tr = np.trace(D)                           # MATLAB: trace -> np.trace
cs = np.cumsum(B, axis=1)                  # MATLAB: cumsum(B, 2) -> np.cumsum(axis=1)
mask_sum = np.sum(B[B > 6])                # MATLAB: sum(B(B > 6)) -> np.sum(B[B > 6])
row_max = np.max(B, axis=1)                # MATLAB: max(B, [], 2)' -> np.max(axis=1)
