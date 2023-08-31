#include <cmath>
#include <vector>

std::vector<double> createLowpassCase(int N) {
  const double wpass_ratio = 0.12 * M_PI;
  const double wstop_ratio = 0.20 * M_PI;
  const double delta0_wpass = 0.025;
  const double delta0_wstop = 0.125;
  const double delta = 20.0 * std::log10(1.0 + delta0_wpass);
  const double delta2 = 20.0 * std::log10(delta0_wstop);

  const int M = 15 * N;
  std::vector<double> omega(M);
  for (int i = 0; i < M; i++) {
    omega[i] = i * std::pi / (M - 1);
  }

  std::vector<std::vector<double>> An(N + 1, std::vector<double>(M));
  for (int i = 0; i < N; i++) {
    for (int j = 0; j < M; j++) {
      An[i + 1][j] = 2.0 * std::cos(omega[j] * i);
    }
  }

  std::vector<double> Ap(N, 1.0);
  for (int i = 0; i < N; i++) {
    Ap[i] += An[i + 1][i];
  }

  double Lp = std::pow(10.0, -delta / 20.0);
  double Up = std::pow(10.0, +delta / 20.0);
  std::vector<double> Sp(N, Sp);

  std::vector<double> omega_new;
  LowpassOracle(Ap, As, Anr, Lpsq, Upsq, &omega_new);

  return omega_new;
}
