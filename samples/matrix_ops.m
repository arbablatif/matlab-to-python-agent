% matrix_ops.m
% Linear algebra and the indexing conventions that trip up MATLAB->Python ports
% (1-based indexing, column-major order, "end", elementwise vs matrix product).
% Written from scratch for the matlab-to-python-agent demo (public, no client data).

A = [4 -2 1; -2 4 -2; 1 -2 4];     % symmetric positive definite
b = [11; -16; 17];

x        = A \ b;                  % solve A*x = b
detA     = det(A);
Ainv     = inv(A);
ev       = sort(eig(A));
residual = norm(A*x - b);

B      = reshape(1:12, 3, 4);      % column-major fill!
B_flat = B(:)';                    % column-major flatten
sub    = B(2:3, [1 end]);          % rows 2-3, first and last column
K      = kron(eye(2), [1 2; 3 4]);

C  = A .* A' + 2;                  % elementwise product
D  = A * A';                       % matrix product
tr = trace(D);
cs = cumsum(B, 2);                 % cumulative sum along rows
mask_sum = sum(B(B > 6));
row_max  = max(B, [], 2)';
