use num_complex::Complex;
use num_traits::Float;

fn create_lowpass_case(N: i32) -> (Complex<f64>, Complex<f64>) {
    const WPASS_RATIO: f64 = 0.12 * std::f64::consts::PI;
    const WSTOP_RATIO: f64 = 0.20 * std::f64::consts::PI;
    const DELTA0_WPASS: f64 = 0.025;
    const DELTA0_WSTOP: f64 = 0.125;
    let delta: Complex<f64> = Complex::new(20.0, 0.0) * std::log10(1.0 + DELTA0_WPASS);
    let delta2: Complex<f64> = Complex::new(20.0, 0.0) * std::log10(DELTA0_WSTOP);

    const M: i32 = 15 * N;
    let mut omega: Vec<Complex<f64>> = vec![];
    for w in 0..M {
        omega.push(Complex::new(w as f64 * std::f64::consts::PI / M as f64, 0.0));
    }

    let mut An: Vec<Vec<Complex<f64>>> = vec![];
    for _ in 0..N {
        let mut row: Vec<Complex<f64>> = vec![];
        for w in omega.iter() {
            row.push(Complex::new(2.0, 0.0) * w.cos());
        }
        An.push(row);
    }

    let Lp: Complex<f64> = Complex::new(pow!(10.0, -delta.re / 20.0), 0.0);
    let Up: Complex<f64> = Complex::new(pow!(10.0, delta.re / 20.0), 0.0);
    let Ap = An[..N].to_vec();

    let Sp: Complex<f64> = Complex::new(pow!(10.0, delta2.re / 20.0), 0.0);
    let As = An[M..(M + N)].to_vec();
    let ind_beg = N - 1;
    let ind_end = M + N;
    let Anr = &An[ind_beg..ind_end];

    let Lpsq = Lp * Lp;
    let Upsq = Up * Up;
    let Spsq = Sp * Sp;

    let omega = LowpassOracle(&Ap, &As, Anr, &Lpsq, &Upsq);
    return (omega, Spsq);
}
