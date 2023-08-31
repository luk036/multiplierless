use ndarray::Array1;
use ndarray::Array2;
use ndarray::s;
use ndarray::stack;
use ndarray::Axis;
use ndarray::concatenate;
use ndarray::linalg::Dot;

fn create_lowpass_case(N: usize) -> (Array1<f64>, f64) {
    let wpass = 0.12 * std::f64::consts::PI;
    let wstop = 0.20 * std::f64::consts::PI;
    let delta0_wpass = 0.025;
    let delta0_wstop = 0.125;
    let delta = 20.0 * (delta0_wpass).log10();
    let delta2 = 20.0 * (delta0_wstop).log10();

    let m = 15 * N;
    let w = Array1::linspace(0.0, std::f64::consts::PI, m);

    let mut An = Array2::zeros((m, N - 1));
    for (i, row) in An.genrows_mut().into_iter().enumerate() {
        for (j, val) in row.iter_mut().enumerate() {
            *val = 2.0 * (w[i] * (j + 1) as f64).cos();
        }
    }

    let A = stack![Axis(1), Array2::ones(m).insert_axis(Axis(1)), An];

    let ind_p = w.iter().enumerate().filter(|(_, &val)| val <= wpass).map(|(i, _)| i).collect::<Vec<_>>();
    let Lp = 10.0f64.powf(-delta / 20.0);
    let Up = 10.0f64.powf(delta / 20.0);
    let Ap = A.slice(s![ind_p, ..]);

    let ind_s = w.iter().enumerate().filter(|(_, &val)| val >= wstop).map(|(i, _)| i).collect::<Vec<_>>();
    let Sp = 10.0f64.powf(delta2 / 20.0);
    let As = A.slice(s![ind_s, ..]);

    let ind_beg = ind_p[ind_p.len() - 1];
    let ind_end = ind_s[0];
    let Anr = A.slice(s![ind_beg + 1..ind_end, ..]);

    let Lpsq = Lp * Lp;
    let Upsq = Up * Up;
    let Spsq = Sp * Sp;

    let omega = lowpass_oracle(Ap, As, Anr, Lpsq, Upsq);
    (omega, Spsq)
}

fn lowpass_oracle(Ap: Array2<f64>, As: Array2<f64>, Anr: Array2<f64>, Lpsq: f64, Upsq: f64) -> Array1<f64> {
    let ApT = Ap.t();
    let AsT = As.t();
    let AnrT = Anr.t();

    let A1 = concatenate![Axis(0), ApT, -ApT, AsT, -AsT];
    let A2 = concatenate![Axis(0), AnrT, -AnrT];
    let A = concatenate![Axis(0), A1, A2];

    let b = Array1::zeros(A.shape()[0]);
    let c = Array1::zeros(A.shape()[1]);

    let mut x = Array1::zeros(A.shape()[1]);
    let mut y = Array1::zeros(A.shape()[0]);

    let mut iter = 0;
    let max_iter = 1000;
    let tol = 1e-6;

    while iter < max_iter {
        let Ax = A.dot(&x);
        let Ay = A.t().dot(&y);

        let primal_res = Ax - b;
        let dual_res = Ay + c;

        let primal_feas = primal_res.iter().map(|&val| val.abs()).sum::<f64>() / (1.0 + b.iter().map(|&val| val.abs()).sum::<f64>());
        let dual_feas = dual_res.iter().map(|&val| val.abs()).sum::<f64>() / (1.0 + c.iter().map(|&val| val.abs()).sum::<f64>());

        let mu = (x.dot(&y) + primal_feas * dual_feas) / (A.shape()[0] as f64);

        let sigma = 0.1;
        let tau = 0.1;

        let dx = (1.0 / (1.0 + sigma)) * (mu * c - Ax);
        let dy = (1.0 / (1.0 + tau)) * (mu * x - Ay);

        let alpha_p = primal_res.iter().zip(dx.iter()).map(|(&res, &dx)| if res < 0.0 { -dx / res } else { std::f64::INFINITY }).fold(std::f64::INFINITY, f64::min);
        let alpha_d = dual_res.iter().zip(dy.iter()).map(|(&res, &dy)| if res < 0.0 { -dy / res } else { std::f64::INFINITY }).fold(std::f64::INFINITY, f64::min);

        let alpha = f64::min(1.0, f64::min(alpha_p, alpha_d));

        x += alpha * dx;
        y += alpha * dy;

        let primal_res_norm = primal_res.iter().map(|&val| val * val).sum::<f64>().sqrt();
        let dual_res_norm = dual_res.iter().map(|&val| val * val).sum::<f64>().sqrt();

        if primal_res_norm < tol && dual_res_norm < tol {
            break;
        }

        iter += 1;
    }

    x
}
