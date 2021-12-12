function [ dc,dcn,reps ] = cholsfact( a, b, rho,q,m )
%Spectral factorization using Cholesky decomposition
%dc.dc*=a.a.rho+b.b*.q
%dcn is normalised spectral factor
%Uses the Toeplitz matrix approach
%T.J.Moir Dec 2019
% we need two polynomials b/a as in ARMAX approach for control.
%no delay is not included in b polynomial - important
%let m be much greater than a or b polynomial lengths eg  12
%note, if q=0 then a is returned as spectral-factor (NOT its mirror image
%in the z-plane).
na=length(a);
nb=length(b);
% Create Teoplitz Matrices for random signal
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% first a polynomial
tr=zeros(1,m);
tr(1)=a(1);
nul=zeros(1,(m-length(a)));
tc=horzcat(a,nul);
A=toeplitz(tc,tr)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Create Teoplitz Matrix for b polynomial
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
tr=zeros(1,m);
tr(1)=b(1);
nul=zeros(1,(m-length(b)));
tc=horzcat(b,nul);
B=toeplitz(tc,tr)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% suffering succotash! - Sylvester matrix is formed below
Sc=A*A'*rho +B*B'*q;
Dc=chol(Sc,'lower');
dc=fliplr(Dc(m,:));
%truncate to required length.
if na>nb
  npar=na;
elseif  nb>na
     npar=nb;
elseif na==nb
    npar=na;
        
end
dc=dc(1:npar)
%normalised version
dcn=dc/dc(1)
%constant term ie dc.dc* = dcn*.dcn*reps
reps=dc(1)^2

