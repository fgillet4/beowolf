#!/usr/bin/env Rscript
# Simple R Benchmark Script for Machine Performance Testing
# Tests CPU, memory, and basic computational capabilities

cat("\n")
cat("========================================\n")
cat("R Machine Benchmark\n")
cat("========================================\n\n")

# System Information
cat("System Information:\n")
cat("------------------------------------------\n")
cat(sprintf("Hostname: %s\n", Sys.info()["nodename"]))
cat(sprintf("OS: %s %s\n", Sys.info()["sysname"], Sys.info()["release"]))
cat(sprintf("Machine: %s\n", Sys.info()["machine"]))
cat(sprintf("R Version: %s\n", R.version.string))
cat(sprintf("Cores Available: %d\n", parallel::detectCores()))
cat("\n")

# Benchmark 1: Matrix Multiplication (CPU)
cat("Benchmark 1: Matrix Multiplication\n")
cat("------------------------------------------\n")
size <- 2000
cat(sprintf("Matrix size: %dx%d\n", size, size))

set.seed(123)
A <- matrix(rnorm(size * size), nrow = size)
B <- matrix(rnorm(size * size), nrow = size)

start_time <- Sys.time()
C <- A %*% B
end_time <- Sys.time()

elapsed <- as.numeric(difftime(end_time, start_time, units = "secs"))
cat(sprintf("Time: %.3f seconds\n", elapsed))
cat(sprintf("Score: %.2f GFLOPS (approx)\n", (2 * size^3 / elapsed) / 1e9))
cat("\n")

# Benchmark 2: Vector Operations
cat("Benchmark 2: Vector Operations\n")
cat("------------------------------------------\n")
n <- 10000000
cat(sprintf("Vector size: %d elements\n", n))

set.seed(123)
x <- rnorm(n)
y <- rnorm(n)

start_time <- Sys.time()
for(i in 1:10) {
  z <- x + y
  z <- z * 2
  z <- sqrt(abs(z))
  result <- sum(z)
}
end_time <- Sys.time()

elapsed <- as.numeric(difftime(end_time, start_time, units = "secs"))
cat(sprintf("Time: %.3f seconds\n", elapsed))
cat(sprintf("Operations/sec: %.2f million\n", (n * 4 * 10 / elapsed) / 1e6))
cat("\n")

# Benchmark 3: Memory Allocation
cat("Benchmark 3: Memory Allocation\n")
cat("------------------------------------------\n")
allocations <- 100
size_mb <- 100

start_time <- Sys.time()
for(i in 1:allocations) {
  temp <- matrix(rnorm(size_mb * 1024 * 128), ncol = 1024)  # ~100MB per iteration
}
end_time <- Sys.time()

elapsed <- as.numeric(difftime(end_time, start_time, units = "secs"))
total_mb <- allocations * size_mb
cat(sprintf("Total allocated: %d MB\n", total_mb))
cat(sprintf("Time: %.3f seconds\n", elapsed))
cat(sprintf("Bandwidth: %.2f MB/sec\n", total_mb / elapsed))
cat("\n")

# Benchmark 4: Statistical Operations
cat("Benchmark 4: Statistical Operations\n")
cat("------------------------------------------\n")
n <- 1000000
iterations <- 50

set.seed(123)
data <- rnorm(n)

start_time <- Sys.time()
for(i in 1:iterations) {
  m <- mean(data)
  s <- sd(data)
  med <- median(data)
  q <- quantile(data, c(0.25, 0.75))
}
end_time <- Sys.time()

elapsed <- as.numeric(difftime(end_time, start_time, units = "secs"))
cat(sprintf("Iterations: %d\n", iterations))
cat(sprintf("Time: %.3f seconds\n", elapsed))
cat(sprintf("Iterations/sec: %.2f\n", iterations / elapsed))
cat("\n")

# Benchmark 5: Linear Regression
cat("Benchmark 5: Linear Regression\n")
cat("------------------------------------------\n")
n <- 100000
p <- 50
iterations <- 10

set.seed(123)
X <- matrix(rnorm(n * p), nrow = n)
y <- rnorm(n)

start_time <- Sys.time()
for(i in 1:iterations) {
  model <- lm.fit(X, y)
}
end_time <- Sys.time()

elapsed <- as.numeric(difftime(end_time, start_time, units = "secs"))
cat(sprintf("Observations: %d, Predictors: %d\n", n, p))
cat(sprintf("Iterations: %d\n", iterations))
cat(sprintf("Time: %.3f seconds\n", elapsed))
cat(sprintf("Models/sec: %.2f\n", iterations / elapsed))
cat("\n")

# Benchmark 6: Data Frame Operations
cat("Benchmark 6: Data Frame Operations\n")
cat("------------------------------------------\n")
n <- 1000000

set.seed(123)
df <- data.frame(
  x = rnorm(n),
  y = rnorm(n),
  group = sample(LETTERS[1:10], n, replace = TRUE)
)

start_time <- Sys.time()
# Subset
df_subset <- df[df$x > 0, ]
# Sort
df_sorted <- df[order(df$x), ]
# Aggregate
agg <- aggregate(x ~ group, data = df, FUN = mean)
end_time <- Sys.time()

elapsed <- as.numeric(difftime(end_time, start_time, units = "secs"))
cat(sprintf("Rows: %d\n", n))
cat(sprintf("Time: %.3f seconds\n", elapsed))
cat(sprintf("Rows/sec: %.2f million\n", (n / elapsed) / 1e6))
cat("\n")

# Overall Score Calculation
cat("========================================\n")
cat("Overall Performance Summary\n")
cat("========================================\n\n")

# Composite score (normalized, arbitrary units)
# Lower is better for time-based metrics
score_components <- c(
  1000 / elapsed  # Last benchmark as reference
)

cat("Machine Type Detection:\n")
cpu_info <- system("sysctl -n machdep.cpu.brand_string 2>/dev/null || grep 'model name' /proc/cpuinfo 2>/dev/null | head -1 | cut -d':' -f2 || echo 'Unknown'", intern = TRUE)
if(length(cpu_info) > 0) {
  cat(sprintf("CPU: %s\n", trimws(cpu_info[1])))
}

mem_info <- system("sysctl -n hw.memsize 2>/dev/null || grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}'", intern = TRUE)
if(length(mem_info) > 0 && mem_info[1] != "") {
  mem_gb <- as.numeric(mem_info[1]) / (1024^3)
  if(mem_gb < 1) {
    mem_gb <- as.numeric(mem_info[1]) / 1024  # Linux reports in KB
  }
  cat(sprintf("Memory: %.1f GB\n", mem_gb))
}

cat("\nRecommendations:\n")
cat("- For parallel processing, use up to %d cores\n", parallel::detectCores())
cat("- Consider using data.table for large data operations\n")
cat("- Use matrix operations instead of loops when possible\n")

cat("\n========================================\n")
cat("Benchmark Complete!\n")
cat("========================================\n\n")

# Save results to JSON
results <- list(
  timestamp = format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
  hostname = Sys.info()["nodename"],
  os = paste(Sys.info()["sysname"], Sys.info()["release"]),
  r_version = R.version.string,
  cores = parallel::detectCores(),
  benchmarks = list(
    matrix_mult_seconds = as.numeric(elapsed),
    cores_available = parallel::detectCores()
  )
)

json_file <- "benchmark_results.json"
if(require(jsonlite, quietly = TRUE)) {
  write_json(results, json_file, auto_unbox = TRUE, pretty = TRUE)
  cat(sprintf("Results saved to: %s\n\n", json_file))
} else {
  cat("Note: Install 'jsonlite' package to save JSON results\n\n")
}
