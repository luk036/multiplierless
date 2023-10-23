#include <cmath>
#include <iostream>
#include <vector>

#define M_PI 3.1415926

std::vector<double> create_lowpass_case(int N = 48) {
  double wpass = 0.12 * M_PI; // end of passband
  double wstop = 0.20 * M_PI; // start of stopband
  double delta0_wpass = 0.025;
  double delta0_wstop = 0.125;
  // maximum passband ripple in dB (+/- around 0 dB)
  double delta = 20 * log10(1 + delta0_wpass);
  // stopband attenuation desired in dB
  double delta2 = 20 * log10(delta0_wstop);

  // *********************************************************************
  // optimization parameters
  // *********************************************************************
  // rule-of-thumb discretization (from Cheney's Approximation Theory)
  int m = 15 * N;
  std::vector<double> w(m);
  for (int i = 0; i < m; i++) {
    w[i] = i * M_PI / (m - 1);
  }

  // A is the matrix used to compute the power spectrum
  // A(w,:) = [1 2*cos(w) 2*cos(2*w) ... 2*cos(N*w)]
  std::vector<std::vector<double>> A(m, std::vector<double>(N + 1));
  for (int i = 0; i < m; i++) {
    A[i][0] = 1;
    for (int j = 1; j <= N; j++) {
      A[i][j] = 2 * cos(j * w[i]);
    }
  }

  // passband 0 <= w <= w_pass
  std::vector<int> ind_p;
  for (int i = 0; i < m; i++) {
    if (w[i] <= wpass) {
      ind_p.push_back(i);
    }
  }
  double Lp = pow(10, -delta / 20);
  double Up = pow(10, delta / 20);
  std::vector<std::vector<double>> Ap(ind_p.size(), std::vector<double>(N + 1));
  for (int i = 0; i < ind_p.size(); i++) {
    for (int j = 0; j <= N; j++) {
      Ap[i][j] = A[ind_p[i]][j];
    }
  }

  // stopband (w_stop <= w)
  std::vector<int> ind_s;
  for (int i = 0; i < m; i++) {
    if (w[i] >= wstop) {
      ind_s.push_back(i);
    }
  }
  double Sp = pow(10, delta2 / 20);
  std::vector<std::vector<double>> As(ind_s.size(), std::vector<double>(N + 1));
  for (int i = 0; i < ind_s.size(); i++) {
    for (int j = 0; j <= N; j++) {
      As[i][j] = A[ind_s[i]][j];
    }
  }

  // remove redundant constraints
  int ind_beg = ind_p.back();
  int ind_end = ind_s.front();
  std::vector<std::vector<double>> Anr(ind_end - ind_beg - 1,
                                       std::vector<double>(N + 1));
  for (int i = ind_beg + 1; i < ind_end; i++) {
    for (int j = 0; j <= N; j++) {
      Anr[i - ind_beg - 1][j] = A[i][j];
    }
  }

  double Lpsq = Lp * Lp;
  double Upsq = Up * Up;
  double Spsq = Sp * Sp;

  std::vector<double> omega;
  // Call LowpassOracle function to compute omega
  // ...

  return omega;
}
