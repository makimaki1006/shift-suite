#!/usr/bin/env python3
"""
Performance Measurement Test
パフォーマンス測定とメモリ使用量分析
"""
import sys
import time
import psutil
import gc
import os
from datetime import datetime
sys.path.append('.')

def get_process_info():
    """現在のプロセス情報を取得"""
    process = psutil.Process(os.getpid())
    return {
        'cpu_percent': process.cpu_percent(),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'memory_percent': process.memory_percent()
    }

def measure_import_performance():
    """dash_app インポート時のパフォーマンス測定"""
    print("=== Import Performance Measurement ===")
    
    start_info = get_process_info()
    start_time = time.time()
    
    try:
        print("Importing dash_app...")
        import dash_app
        
        end_time = time.time()
        end_info = get_process_info()
        
        import_time = end_time - start_time
        memory_increase = end_info['memory_mb'] - start_info['memory_mb']
        
        print(f"Import time: {import_time:.2f} seconds")
        print(f"Memory before: {start_info['memory_mb']:.1f} MB")
        print(f"Memory after: {end_info['memory_mb']:.1f} MB") 
        print(f"Memory increase: {memory_increase:.1f} MB")
        
        return {
            'success': True,
            'import_time': import_time,
            'memory_increase': memory_increase,
            'final_memory': end_info['memory_mb']
        }
        
    except Exception as e:
        end_time = time.time()
        print(f"Import failed: {e}")
        return {
            'success': False,
            'import_time': end_time - start_time,
            'error': str(e)
        }

def measure_tab_creation_performance():
    """タブ作成処理のパフォーマンス測定"""
    print("\n=== Tab Creation Performance ===")
    
    try:
        import dash_app
        
        # Warm-up run
        print("Warming up...")
        dash_app.create_shortage_tab()
        gc.collect()
        
        # Performance measurement
        print("Measuring performance...")
        
        times = []
        memory_usages = []
        
        for i in range(5):
            start_info = get_process_info()
            start_time = time.time()
            
            result = dash_app.create_shortage_tab(f"test_scenario_{i}")
            
            end_time = time.time()
            end_info = get_process_info()
            
            execution_time = end_time - start_time
            times.append(execution_time)
            memory_usages.append(end_info['memory_mb'])
            
            print(f"  Run {i+1}: {execution_time:.3f}s, Memory: {end_info['memory_mb']:.1f}MB")
            
            # Cleanup
            del result
            gc.collect()
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        avg_memory = sum(memory_usages) / len(memory_usages)
        
        print(f"\nPerformance Summary:")
        print(f"Average time: {avg_time:.3f}s")
        print(f"Min time: {min_time:.3f}s")
        print(f"Max time: {max_time:.3f}s")
        print(f"Average memory: {avg_memory:.1f}MB")
        
        return {
            'success': True,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'avg_memory': avg_memory,
            'times': times
        }
        
    except Exception as e:
        print(f"Tab creation performance test failed: {e}")
        return {'success': False, 'error': str(e)}

def measure_data_access_performance():
    """データアクセス処理のパフォーマンス測定"""
    print("\n=== Data Access Performance ===")
    
    try:
        import dash_app
        
        data_keys = [
            'shortage_role_summary',
            'proportional_abolition_role_summary'
        ]
        
        results = {}
        
        for key in data_keys:
            print(f"Testing data access: {key}")
            
            times = []
            for i in range(3):
                start_time = time.time()
                data = dash_app.data_get(key)
                end_time = time.time()
                
                access_time = end_time - start_time
                times.append(access_time)
                
                if data is not None:
                    print(f"  Run {i+1}: {access_time:.3f}s, Shape: {data.shape}")
                else:
                    print(f"  Run {i+1}: {access_time:.3f}s, Data: None")
            
            avg_time = sum(times) / len(times)
            results[key] = {
                'avg_time': avg_time,
                'times': times,
                'data_available': data is not None
            }
            
            print(f"  Average: {avg_time:.3f}s")
        
        return {
            'success': True,
            'results': results
        }
        
    except Exception as e:
        print(f"Data access performance test failed: {e}")
        return {'success': False, 'error': str(e)}

def measure_memory_usage_pattern():
    """メモリ使用パターンの測定"""
    print("\n=== Memory Usage Pattern ===")
    
    try:
        import dash_app
        
        # Initial memory
        initial_info = get_process_info()
        print(f"Initial memory: {initial_info['memory_mb']:.1f} MB")
        
        memory_snapshots = [initial_info['memory_mb']]
        
        # Create tabs and measure memory
        for i in range(10):
            result = dash_app.create_shortage_tab(f"memory_test_{i}")
            current_info = get_process_info()
            memory_snapshots.append(current_info['memory_mb'])
            
            if i % 2 == 0:
                print(f"  After {i+1} tabs: {current_info['memory_mb']:.1f} MB")
            
            # Cleanup every few iterations
            if i % 3 == 2:
                del result
                gc.collect()
        
        # Force cleanup
        gc.collect()
        final_info = get_process_info()
        memory_snapshots.append(final_info['memory_mb'])
        
        max_memory = max(memory_snapshots)
        min_memory = min(memory_snapshots)
        final_memory = final_info['memory_mb']
        
        print(f"\nMemory Pattern Summary:")
        print(f"Initial: {initial_info['memory_mb']:.1f} MB")
        print(f"Maximum: {max_memory:.1f} MB")
        print(f"Final: {final_memory:.1f} MB")
        print(f"Peak increase: {max_memory - initial_info['memory_mb']:.1f} MB")
        print(f"Net increase: {final_memory - initial_info['memory_mb']:.1f} MB")
        
        return {
            'success': True,
            'initial_memory': initial_info['memory_mb'],
            'max_memory': max_memory,
            'final_memory': final_memory,
            'peak_increase': max_memory - initial_info['memory_mb'],
            'net_increase': final_memory - initial_info['memory_mb'],
            'snapshots': memory_snapshots
        }
        
    except Exception as e:
        print(f"Memory usage pattern test failed: {e}")
        return {'success': False, 'error': str(e)}

def analyze_system_impact():
    """システム全体への影響分析"""
    print("\n=== System Impact Analysis ===")
    
    try:
        # System info before
        sys_before = {
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            'memory_available': psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
            'cpu_percent': psutil.cpu_percent(interval=1)
        }
        
        print(f"System Info:")
        print(f"  CPU cores: {sys_before['cpu_count']}")
        print(f"  Total memory: {sys_before['memory_total']:.1f} GB")
        print(f"  Available memory: {sys_before['memory_available']:.1f} GB")
        print(f"  CPU usage: {sys_before['cpu_percent']:.1f}%")
        
        # Process impact
        process = psutil.Process(os.getpid())
        
        print(f"\nProcess Impact:")
        print(f"  Process memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        print(f"  Memory percentage: {process.memory_percent():.1f}%")
        
        return {
            'success': True,
            'system_info': sys_before,
            'process_impact': {
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent()
            }
        }
        
    except Exception as e:
        print(f"System impact analysis failed: {e}")
        return {'success': False, 'error': str(e)}

def main():
    print("=== ShiftAnalysis Performance Measurement ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        'import_performance': None,
        'tab_creation_performance': None,
        'data_access_performance': None,
        'memory_usage_pattern': None,
        'system_impact': None
    }
    
    # Run all measurements
    results['import_performance'] = measure_import_performance()
    results['tab_creation_performance'] = measure_tab_creation_performance()
    results['data_access_performance'] = measure_data_access_performance()
    results['memory_usage_pattern'] = measure_memory_usage_pattern()
    results['system_impact'] = analyze_system_impact()
    
    # Overall assessment
    print("\n" + "=" * 60)
    print("PERFORMANCE ASSESSMENT")
    print("=" * 60)
    
    # Import assessment
    if results['import_performance']['success']:
        import_time = results['import_performance']['import_time']
        import_memory = results['import_performance']['memory_increase']
        
        if import_time < 10:
            print(f"Import speed: EXCELLENT ({import_time:.1f}s)")
        elif import_time < 30:
            print(f"Import speed: GOOD ({import_time:.1f}s)")
        else:
            print(f"Import speed: SLOW ({import_time:.1f}s)")
        
        if import_memory < 100:
            print(f"Import memory: EXCELLENT ({import_memory:.1f}MB)")
        elif import_memory < 300:
            print(f"Import memory: GOOD ({import_memory:.1f}MB)")
        else:
            print(f"Import memory: HIGH ({import_memory:.1f}MB)")
    
    # Tab creation assessment  
    if results['tab_creation_performance']['success']:
        avg_time = results['tab_creation_performance']['avg_time']
        
        if avg_time < 0.1:
            print(f"Tab creation: EXCELLENT ({avg_time:.3f}s avg)")
        elif avg_time < 1.0:
            print(f"Tab creation: GOOD ({avg_time:.3f}s avg)")
        else:
            print(f"Tab creation: SLOW ({avg_time:.3f}s avg)")
    
    # Data access assessment
    if results['data_access_performance']['success']:
        shortage_time = results['data_access_performance']['results']['shortage_role_summary']['avg_time']
        prop_time = results['data_access_performance']['results']['proportional_abolition_role_summary']['avg_time']
        
        avg_data_time = (shortage_time + prop_time) / 2
        
        if avg_data_time < 0.05:
            print(f"Data access: EXCELLENT ({avg_data_time:.3f}s avg)")
        elif avg_data_time < 0.2:
            print(f"Data access: GOOD ({avg_data_time:.3f}s avg)")
        else:
            print(f"Data access: SLOW ({avg_data_time:.3f}s avg)")
    
    # Memory assessment
    if results['memory_usage_pattern']['success']:
        peak_increase = results['memory_usage_pattern']['peak_increase']
        
        if peak_increase < 50:
            print(f"Memory efficiency: EXCELLENT ({peak_increase:.1f}MB peak)")
        elif peak_increase < 200:
            print(f"Memory efficiency: GOOD ({peak_increase:.1f}MB peak)")
        else:
            print(f"Memory efficiency: HIGH ({peak_increase:.1f}MB peak)")
    
    # Overall conclusion
    success_count = sum(1 for r in results.values() if r and r.get('success', False))
    
    print(f"\nOverall: {success_count}/5 measurements successful")
    
    if success_count >= 4:
        print("CONCLUSION: System shows GOOD performance characteristics")
        print("- Ready for production use with current load expectations")
    elif success_count >= 3:
        print("CONCLUSION: System shows ACCEPTABLE performance")
        print("- May need optimization for high-load scenarios")
    else:
        print("CONCLUSION: System shows POOR performance")
        print("- Requires optimization before production use")
    
    return results

if __name__ == "__main__":
    main()