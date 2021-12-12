% Test Cholesky decomposition spectral factorization
% uses lower triangular Toeplitz matrices
a=[1 2 3 4];
b=[2 4 6];
rho=1;
q=1;
m=10;
%Spectral factor calculated here
%dc.dc*=a.a.rho+b.b*.q
[ dc,dcn,reps ] = cholsfact( a, b, rho,q,m )
% answer below
disp('Spectral factor is')
dc
%normalised version
disp('Normalised spectral-factor')
dcn
%constant term ie dc.dc* = dcn*.dcn*reps
reps
