#include <cmath>
#include <iostream>
#include <vector>

std::vector<double> create_lowpass_case(int N = 48) {
  double wpass = 0.12 * M_PI;
  double wstop = 0.20 * M_PI;
  double delta0_wpass = 0.025;
  double delta0_wstop = 0.125;

  double delta = 20 * log10(1 + delta0_wpass);

  double delta2 = 20 * log10(delta0_wstop);

  int m = 15 * N;
  std::vector<double> w(m);
  for (int i = 0; i < m; i++) {
    w[i] = i * M_PI / (m - 1);
  }

  std::vector<std::vector<double>> An(m, std::vector<double>(N));
  for (int i = 0; i < m; i++) {
    for (int j = 0; j < N; j++) {
      An[i][j] = 2 * cos(w[i] * (j + 1));
    }
  }

  std::vector<std::vector<double>> A(m, std::vector<double>(N + 1));
  for (int i = 0; i < m; i++) {
    A[i][0] = 1;
    for (int j = 0; j < N; j++) {
      A[i][j + 1] = An[i][j];
    }
  }

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
    for (int j = 0; j < N + 1; j++) {
      Ap[i][j] = A[ind_p[i]][j];
    }
  }

  std::vector<int> ind_s;
  for (int i = 0; i < m; i++) {
    if (w[i] >= wstop) {
      ind_s.push_back(i);
    }
  }

  double Sp = pow(10, delta2 / 20);

  std::vector<std::vector<double>> As(ind_s.size(), std::vector<double>(N + 1));
  for (int i = 0; i < ind_s.size(); i++) {
    for (int j = 0; j < N + 1; j++) {
      As[i][j] = A[ind_s[i]][j];
    }
  }

  int ind_beg = ind_p[ind_p.size() - 1];
  int ind_end = ind_s[0];

  std::vector<std::vector<double>> Anr(ind_end - ind_beg - 1,
                                       std::vector<double>(N + 1));
  for (int i = ind_beg + 1; i < ind_end; i++) {
    for (int j = 0; j < N + 1; j++) {
      Anr[i - ind_beg - 1][j] = A[i][j];
    }
  }

  double Lpsq = Lp * Lp;
  double Upsq = Up * Up;
  double Spsq = Sp * Sp;

  std::vector<double> omega;
  omega.push_back(Lpsq);
  omega.push_back(Upsq);

  return omega;
}
