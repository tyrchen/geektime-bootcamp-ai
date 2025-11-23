//! 无锁环形缓冲区模块
//!
//! 使用对象池模式减少内存分配，提供高性能的音频数据传输

use crossbeam::queue::ArrayQueue;
use std::sync::Arc;
use tracing::warn;

/// 无锁环形缓冲区
///
/// 使用 crossbeam 的 ArrayQueue 实现线程安全的无锁队列
/// 结合对象池模式复用 Vec，减少内存分配开销
#[derive(Clone)]
pub struct RingBuffer {
    queue: Arc<ArrayQueue<Vec<f32>>>,
    pool: Arc<ArrayQueue<Vec<f32>>>,
    capacity: usize,
    buffer_size: usize,
}

impl RingBuffer {
    /// 创建新的环形缓冲区
    ///
    /// # Arguments
    /// * `capacity` - 队列容量（可以存储多少个音频块）
    /// * `buffer_size` - 每个音频块的大小（采样点数量）
    ///
    /// # Example
    /// ```
    /// use raflow_lib::audio::RingBuffer;
    ///
    /// // 创建可以存储 100 个音频块的缓冲区，每个块 480 个采样点
    /// let buffer = RingBuffer::new(100, 480);
    /// ```
    pub fn new(capacity: usize, buffer_size: usize) -> Self {
        let queue = Arc::new(ArrayQueue::new(capacity));
        let pool = Arc::new(ArrayQueue::new(capacity));

        // 预分配缓冲区对象到对象池
        for _ in 0..capacity {
            let buffer = Vec::with_capacity(buffer_size);
            let _ = pool.push(buffer);
        }

        Self {
            queue,
            pool,
            capacity,
            buffer_size,
        }
    }

    /// 推送音频数据到缓冲区（生产者端）
    ///
    /// # Arguments
    /// * `data` - 音频采样数据
    ///
    /// # Returns
    /// * `true` - 推送成功
    /// * `false` - 队列已满，推送失败
    pub fn push(&self, data: &[f32]) -> bool {
        // 从对象池获取 Vec
        if let Some(mut buffer) = self.pool.pop() {
            buffer.clear();
            buffer.extend_from_slice(data);
            self.queue.push(buffer).is_ok()
        } else {
            // 对象池耗尽，分配新 Vec（降级处理）
            warn!("Buffer pool exhausted, allocating new Vec");
            self.queue.push(data.to_vec()).is_ok()
        }
    }

    /// 从缓冲区弹出音频数据（消费者端）
    ///
    /// # Returns
    /// * `Some(Vec<f32>)` - 成功获取音频数据
    /// * `None` - 队列为空
    pub fn pop(&self) -> Option<Vec<f32>> {
        self.queue.pop()
    }

    /// 回收 Vec 到对象池
    ///
    /// 用于将处理完的音频缓冲区归还到对象池，供后续复用
    pub fn recycle(&self, mut buffer: Vec<f32>) {
        buffer.clear();
        if buffer.capacity() == self.buffer_size {
            let _ = self.pool.push(buffer);
        }
        // 如果容量不匹配，直接丢弃让 GC 回收
    }

    /// 获取当前队列长度
    pub fn len(&self) -> usize {
        self.queue.len()
    }

    /// 检查队列是否为空
    pub fn is_empty(&self) -> bool {
        self.queue.is_empty()
    }

    /// 获取队列容量
    pub fn capacity(&self) -> usize {
        self.capacity
    }

    /// 获取对象池剩余数量
    pub fn pool_available(&self) -> usize {
        self.pool.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_ring_buffer_creation() {
        let buffer = RingBuffer::new(10, 100);
        assert_eq!(buffer.capacity(), 10);
        assert_eq!(buffer.len(), 0);
        assert!(buffer.is_empty());
    }

    #[test]
    fn test_push_pop() {
        let buffer = RingBuffer::new(5, 10);
        let data = vec![1.0, 2.0, 3.0, 4.0, 5.0];

        // 推送数据
        assert!(buffer.push(&data));
        assert_eq!(buffer.len(), 1);
        assert!(!buffer.is_empty());

        // 弹出数据
        let popped = buffer.pop();
        assert!(popped.is_some());
        assert_eq!(popped.unwrap(), data);
        assert_eq!(buffer.len(), 0);
        assert!(buffer.is_empty());
    }

    #[test]
    fn test_buffer_full() {
        let buffer = RingBuffer::new(3, 10);
        let data = vec![1.0; 10];

        // 填满缓冲区
        assert!(buffer.push(&data));
        assert!(buffer.push(&data));
        assert!(buffer.push(&data));

        // 再推送应该失败
        assert!(!buffer.push(&data));
    }

    #[test]
    fn test_recycle() {
        let buffer = RingBuffer::new(5, 10);
        let data = vec![1.0; 10];

        let initial_pool = buffer.pool_available();

        // 推送并弹出
        buffer.push(&data);
        let popped = buffer.pop().unwrap();

        // 回收
        buffer.recycle(popped);

        // 对象池应该恢复
        assert_eq!(buffer.pool_available(), initial_pool);
    }

    #[test]
    fn test_concurrent_access() {
        let buffer = RingBuffer::new(100, 10);
        let buffer_clone = buffer.clone();

        // 生产者线程
        let producer = thread::spawn(move || {
            for i in 0..50 {
                let data = vec![i as f32; 10];
                while !buffer_clone.push(&data) {
                    thread::yield_now();
                }
            }
        });

        // 消费者线程
        let consumer = thread::spawn(move || {
            let mut count = 0;
            while count < 50 {
                if let Some(_data) = buffer.pop() {
                    count += 1;
                }
                thread::yield_now();
            }
            count
        });

        producer.join().unwrap();
        let consumed = consumer.join().unwrap();

        assert_eq!(consumed, 50);
    }

    #[test]
    fn test_object_pool_efficiency() {
        let buffer = RingBuffer::new(10, 100);
        let data = vec![1.0; 100];

        // 初始对象池应该是满的
        let initial_pool = buffer.pool_available();
        assert_eq!(initial_pool, 10);

        // 推送并弹出
        buffer.push(&data);
        let popped = buffer.pop().unwrap();

        // 对象池减少了 1
        assert_eq!(buffer.pool_available(), initial_pool - 1);

        // 回收后恢复
        buffer.recycle(popped);
        assert_eq!(buffer.pool_available(), initial_pool);
    }
}
