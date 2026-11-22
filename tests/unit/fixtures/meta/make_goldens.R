# Generates tests/unit/fixtures/meta/metafor-goldens.json once, on a maintainer machine with R and metafor.
# REML is fitted with a tight convergence threshold (metafor's default stops at 1e-5, which leaves ~1e-4 relative
# slack in tau2); the Python estimator solves the REML equation to machine precision.
# Run from the repository root:  Rscript tests/unit/fixtures/meta/make_goldens.R
# Inputs: metafor's example datasets dat.bcg and dat.normand1999, and one small constructed zero-cell set
# written below. Every input is written into the JSON next to the results, so the Python tests read their
# inputs from the file and no number is typed by hand. The unit suite never needs R.
suppressPackageStartupMessages(library(metafor))

num <- function(x) if (length(x) == 0 || is.null(x) || is.na(x[1])) "null" else formatC(x[1], digits = 15, format = "g")
arr <- function(x) paste0("[", paste(vapply(x, num, ""), collapse = ", "), "]")
q <- function(x) paste0('"', gsub('"', '\\\\"', as.character(x)), '"')

studies2x2 <- function(id, a, n1, c, n2)
  paste0("[", paste(sprintf('{"study": %s, "a": %d, "n1": %d, "c": %d, "n2": %d}', vapply(as.character(id), q, ""),
                            as.integer(a), as.integer(n1), as.integer(c), as.integer(n2)), collapse = ", "), "]")

summ <- function(r) {
  tau2 <- if (is.null(r$tau2)) 0 else r$tau2
  re <- !is.null(r$method) && r$method %in% c("REML", "DL")
  pi <- if (re && r$k >= 3) r$b[1] + c(-1, 1) * qt(0.975, r$k - 2) * sqrt(tau2 + r$se^2) else NULL
  sprintf('"estimate": %s, "se": %s, "ci": %s, "p": %s, "tau2": %s, "i2": %s, "q": %s, "q_p": %s, "pi": %s, "k": %d',
          num(r$b[1]), num(r$se), arr(c(r$ci.lb, r$ci.ub)), num(r$pval), num(tau2), num(r$I2), num(r$QE),
          num(r$QEp), if (is.null(pi)) "null" else arr(pi), as.integer(r$k))
}
case <- function(name, measure, model, hksj, studies, body)
  sprintf('%s: {"measure": %s, "model": %s, "hksj": %s, "studies": %s, %s}', q(name), q(measure), q(model),
          if (hksj) "true" else "false", studies, body)

bcg <- dat.bcg
b2 <- studies2x2(bcg$trial, bcg$tpos, bcg$tpos + bcg$tneg, bcg$cpos, bcg$cpos + bcg$cneg)
es2 <- function(measure, data = bcg) escalc(measure = measure, ai = tpos, bi = tneg, ci = cpos, di = cneg,
                                            data = data, add = 1/2, to = "only0", drop00 = TRUE)
re2 <- function(measure, method, test = "z", data = bcg) rma(yi, vi, data = es2(measure, data), method = method, test = test, control = list(threshold = 1e-10, maxiter = 1000))

cases <- c(
  case("bcg_rr_reml", "RR", "RE-REML", FALSE, b2, summ(re2("RR", "REML"))),
  case("bcg_rr_dl", "RR", "RE-DL", FALSE, b2, summ(re2("RR", "DL"))),
  case("bcg_or_reml_hksj", "OR", "RE-REML", TRUE, b2, summ(re2("OR", "REML", "knha"))),
  case("bcg_rd_reml", "RD", "RE-REML", FALSE, b2, summ(re2("RD", "REML"))),
  case("bcg_or_ce_iv", "OR", "CE-IV", FALSE, b2, summ(re2("OR", "FE"))),
  case("bcg_or_mh", "OR", "CE-MH", FALSE, b2,
       summ(rma.mh(ai = tpos, bi = tneg, ci = cpos, di = cneg, data = bcg, measure = "OR"))),
  case("bcg_rr_mh", "RR", "CE-MH", FALSE, b2,
       summ(rma.mh(ai = tpos, bi = tneg, ci = cpos, di = cneg, data = bcg, measure = "RR")))
)

er <- es2("RR")
eg <- coef(summary(lm(yi ~ sqrt(vi), weights = 1 / vi, data = er)))[2, ]
cases <- c(cases, case("bcg_rr_egger", "RR", "RE-REML", FALSE, b2,
  sprintf('"egger": {"intercept": %s, "se": %s, "t": %s, "p": %s}', num(eg[1]), num(eg[2]), num(eg[3]), num(eg[4]))))

lev <- sort(unique(as.character(bcg$alloc)))
fits <- lapply(lev, function(l) re2("RR", "REML", data = bcg[bcg$alloc == l, ]))
qb <- rma(yi = sapply(fits, function(f) f$b[1]), sei = sapply(fits, function(f) f$se), method = "FE")
cases <- c(cases, case("bcg_rr_subgroup_alloc", "RR", "RE-REML", FALSE, b2, sprintf(
  '"factor": {%s}, "levels": {%s}, "qb": %s, "qb_df": %d, "qb_p": %s',
  paste(sprintf("%s: %s", vapply(as.character(bcg$trial), q, ""), vapply(as.character(bcg$alloc), q, "")), collapse = ", "),
  paste(sprintf("%s: {%s}", vapply(lev, q, ""), vapply(fits, summ, "")), collapse = ", "),
  num(qb$QE), length(lev) - 1L, num(qb$QEp))))

l1 <- leave1out(re2("RR", "REML"))
cases <- c(cases, case("bcg_rr_loo", "RR", "RE-REML", FALSE, b2, sprintf('"loo": [%s]', paste(
  sprintf('{"omit": %s, "estimate": %s, "ci": %s}', vapply(as.character(bcg$trial), q, ""),
          vapply(l1$estimate, num, ""), mapply(function(a, b) arr(c(a, b)), l1$ci.lb, l1$ci.ub)), collapse = ", "))))

nd <- dat.normand1999
nds <- paste0("[", paste(sprintf('{"study": %s, "m1": %s, "sd1": %s, "n1": %d, "m2": %s, "sd2": %s, "n2": %d}',
  vapply(as.character(nd$study), q, ""), vapply(nd$m1i, num, ""), vapply(nd$sd1i, num, ""), as.integer(nd$n1i),
  vapply(nd$m2i, num, ""), vapply(nd$sd2i, num, ""), as.integer(nd$n2i)), collapse = ", "), "]")
cont <- function(measure) rma(yi, vi, method = "REML", data = escalc(measure = measure, m1i = m1i, sd1i = sd1i,
  n1i = n1i, m2i = m2i, sd2i = sd2i, n2i = n2i, data = nd), control = list(threshold = 1e-10, maxiter = 1000))
cases <- c(cases, case("normand_md_reml", "MD", "RE-REML", FALSE, nds, summ(cont("MD"))),
           case("normand_smd_reml", "SMD", "RE-REML", FALSE, nds, summ(cont("SMD"))))

zc <- data.frame(study = c("Z1", "Z2", "Z3", "Z4", "Z5"), a = c(0, 3, 5, 0, 7), n1 = c(20, 25, 30, 15, 40),
                 c = c(2, 6, 4, 0, 12), n2 = c(20, 24, 31, 15, 38))
zes <- escalc(measure = "OR", ai = a, bi = n1 - a, ci = c, di = n2 - c, data = zc, add = 1/2, to = "only0", drop00 = TRUE)
cases <- c(cases, case("zero_cell_or_reml", "OR", "RE-REML", FALSE, studies2x2(zc$study, zc$a, zc$n1, zc$c, zc$n2),
                       summ(rma(yi, vi, data = zes, method = "REML", control = list(threshold = 1e-10, maxiter = 1000)))))

eng <- sprintf("%s; metafor %s", R.version.string, as.character(packageVersion("metafor")))
txt <- c("{", sprintf('  "engine": %s,', q(eng)), '  "script": "tests/unit/fixtures/meta/make_goldens.R",',
         '  "cases": {', paste0("    ", paste(cases, collapse = ",\n    ")), "  }", "}")
con <- file("tests/unit/fixtures/meta/metafor-goldens.json", open = "wb")
writeLines(txt, con, sep = "\n")
close(con)
