export const money = n => new Intl.NumberFormat('en-IN',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n);
export const pct = n => `${Math.round(n * 100)}%`;
export const num = n => new Intl.NumberFormat('en-IN').format(n);
export const perBbl = n => `$${Math.round(n)}/bbl`;