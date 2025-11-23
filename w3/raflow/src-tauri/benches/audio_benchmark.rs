use criterion::{Criterion, Throughput, criterion_group, criterion_main};
use raflow_lib::audio::{AudioResampler, Quality, RingBuffer};
use std::hint::black_box;

fn bench_resampler(c: &mut Criterion) {
    let mut group = c.benchmark_group("resampler");
    group.throughput(Throughput::Elements(480));

    // 测试不同质量级别的性能
    for quality in &[Quality::Low, Quality::Medium, Quality::High] {
        let quality_name = format!("{:?}", quality);

        group.bench_function(&quality_name, |b| {
            let mut resampler = AudioResampler::new(48000, 16000, 480, 1, *quality).unwrap();
            let input = vec![0.5f32; 480];

            // 预热
            for _ in 0..3 {
                let _ = resampler.process(&input);
            }

            b.iter(|| {
                let output = resampler.process(black_box(&input)).unwrap();
                black_box(output);
            });
        });
    }

    group.finish();
}

fn bench_quantize(c: &mut Criterion) {
    let mut group = c.benchmark_group("quantize");
    group.throughput(Throughput::Elements(160));

    let samples = vec![0.5f32; 160];

    group.bench_function("f32_to_i16", |b| {
        b.iter(|| {
            let output = AudioResampler::quantize_to_i16(black_box(&samples));
            black_box(output);
        });
    });

    group.finish();
}

fn bench_rms_calculation(c: &mut Criterion) {
    let mut group = c.benchmark_group("rms");
    group.throughput(Throughput::Elements(480));

    let samples = vec![0.5f32; 480];

    group.bench_function("calculate_rms", |b| {
        b.iter(|| {
            let rms = AudioResampler::calculate_rms(black_box(&samples));
            black_box(rms);
        });
    });

    group.finish();
}

fn bench_ring_buffer(c: &mut Criterion) {
    let mut group = c.benchmark_group("ring_buffer");

    let buffer = RingBuffer::new(100, 480);
    let data = vec![0.5f32; 480];

    group.bench_function("push", |b| {
        b.iter(|| {
            buffer.push(black_box(&data));
        });
    });

    // 填充一些数据用于 pop 测试
    for _ in 0..50 {
        buffer.push(&data);
    }

    group.bench_function("pop", |b| {
        b.iter(|| {
            let output = buffer.pop();
            black_box(output);
        });
    });

    group.finish();
}

fn bench_end_to_end(c: &mut Criterion) {
    let mut group = c.benchmark_group("end_to_end");
    group.throughput(Throughput::Elements(480));

    let buffer = RingBuffer::new(100, 480);
    let mut resampler = AudioResampler::new(48000, 16000, 480, 1, Quality::High).unwrap();
    let input = vec![0.5f32; 480];

    // 预热
    for _ in 0..3 {
        let _ = resampler.process(&input);
    }

    group.bench_function("capture_to_i16", |b| {
        b.iter(|| {
            // 模拟完整流程：推送 -> 弹出 -> 重采样 -> 量化
            buffer.push(black_box(&input));
            if let Some(audio_chunk) = buffer.pop() {
                if let Ok(resampled) = resampler.process(&audio_chunk) {
                    let i16_samples = AudioResampler::quantize_to_i16(&resampled);
                    black_box(i16_samples);
                }
                buffer.recycle(audio_chunk);
            }
        });
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_resampler,
    bench_quantize,
    bench_rms_calculation,
    bench_ring_buffer,
    bench_end_to_end
);
criterion_main!(benches);
