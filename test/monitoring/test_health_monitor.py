"""
Comprehensive Test Suite for Health Monitor
Tests all health checks, monitoring, and alerting functionality
"""

import pytest
import asyncio
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import time

from src.serena.monitoring.health_monitor import (
    HealthMonitor,
    HealthStatus,
    ComponentType,
    HealthCheck,
    HealthResult,
    SystemMetrics
)


class TestHealthMonitor:
    """Comprehensive test suite for HealthMonitor"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def monitor(self, temp_config_dir):
        """Create HealthMonitor instance for testing"""
        return HealthMonitor(config_dir=temp_config_dir)
    
    def test_initialization(self, monitor):
        """Test HealthMonitor initialization"""
        assert isinstance(monitor, HealthMonitor)
        assert monitor.config_dir.exists()
        assert len(monitor.health_checks) == 9  # All health checks
        assert len(monitor.health_results) == 0
        assert len(monitor.metrics_history) == 0
        assert monitor.monitoring_active is False
        
        # Verify all health check types are loaded
        expected_checks = {
            "system_cpu", "system_memory", "system_disk", "system_load",
            "service_ports", "agent_processes", "mcp_tools", 
            "network_connectivity", "storage_health"
        }
        assert set(monitor.health_checks.keys()) == expected_checks
    
    def test_health_check_configurations(self, monitor):
        """Test that all health checks are properly configured"""
        for check_name, check_config in monitor.health_checks.items():
            assert isinstance(check_config, HealthCheck)
            assert check_config.name
            assert check_config.description
            assert check_config.component_type in ComponentType
            assert check_config.check_function
            assert check_config.interval_seconds > 0
            assert check_config.timeout_seconds > 0
            assert isinstance(check_config.enabled, bool)
            assert isinstance(check_config.critical, bool)
            assert isinstance(check_config.thresholds, dict)
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring"""
        # Start monitoring
        await monitor.start_monitoring()
        assert monitor.monitoring_active is True
        assert monitor.monitoring_task is not None
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor.monitoring_active is False
    
    @pytest.mark.asyncio
    async def test_start_monitoring_already_active(self, monitor):
        """Test starting monitoring when already active"""
        await monitor.start_monitoring()
        
        # Try to start again
        await monitor.start_monitoring()  # Should not raise error
        assert monitor.monitoring_active is True
        
        await monitor.stop_monitoring()


class TestHealthChecks:
    """Test individual health check implementations"""
    
    @pytest.fixture
    def monitor(self):
        return HealthMonitor()
    
    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    async def test_check_cpu_usage_healthy(self, mock_cpu, monitor):
        """Test CPU usage check - healthy state"""
        mock_cpu.return_value = 50.0
        
        check = monitor.health_checks["system_cpu"]
        result = await monitor.check_cpu_usage(check)
        
        assert isinstance(result, HealthResult)
        assert result.status == HealthStatus.HEALTHY
        assert "50.0%" in result.message
        assert result.metrics["cpu_percent"] == 50.0
    
    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    async def test_check_cpu_usage_warning(self, mock_cpu, monitor):
        """Test CPU usage check - warning state"""
        mock_cpu.return_value = 85.0
        
        check = monitor.health_checks["system_cpu"]
        result = await monitor.check_cpu_usage(check)
        
        assert result.status == HealthStatus.WARNING
        assert "WARNING" in result.message
    
    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    async def test_check_cpu_usage_critical(self, mock_cpu, monitor):
        """Test CPU usage check - critical state"""
        mock_cpu.return_value = 98.0
        
        check = monitor.health_checks["system_cpu"]
        result = await monitor.check_cpu_usage(check)
        
        assert result.status == HealthStatus.CRITICAL
        assert "CRITICAL" in result.message
    
    @pytest.mark.asyncio
    @patch('psutil.virtual_memory')
    async def test_check_memory_usage_healthy(self, mock_memory, monitor):
        """Test memory usage check - healthy state"""
        mock_memory.return_value = Mock(
            percent=60.0,
            total=8589934592,
            available=3435973836,
            used=5153960756
        )
        
        check = monitor.health_checks["system_memory"]
        result = await monitor.check_memory_usage(check)
        
        assert result.status == HealthStatus.HEALTHY
        assert "60.0%" in result.message
        assert result.metrics["memory_percent"] == 60.0
        assert result.metrics["memory_total"] == 8589934592
    
    @pytest.mark.asyncio
    @patch('psutil.disk_usage')
    async def test_check_disk_usage_healthy(self, mock_disk, monitor):
        """Test disk usage check - healthy state"""
        mock_disk.return_value = Mock(
            total=1000000000,
            used=500000000,
            free=500000000
        )
        
        check = monitor.health_checks["system_disk"]
        result = await monitor.check_disk_usage(check)
        
        assert result.status == HealthStatus.HEALTHY
        assert "50.0%" in result.message
        assert result.metrics["disk_percent"] == 50.0
    
    @pytest.mark.asyncio
    @patch('psutil.getloadavg')
    async def test_check_load_average_healthy(self, mock_load, monitor):
        """Test load average check - healthy state"""
        mock_load.return_value = (1.0, 1.2, 1.1)
        
        check = monitor.health_checks["system_load"]
        result = await monitor.check_load_average(check)
        
        assert result.status == HealthStatus.HEALTHY
        assert "1.00" in result.message
        assert result.metrics["load_1min"] == 1.0
        assert result.metrics["load_5min"] == 1.2
        assert result.metrics["load_15min"] == 1.1
    
    @pytest.mark.asyncio
    @patch('psutil.net_connections')
    async def test_check_service_ports_healthy(self, mock_connections, monitor):
        """Test service ports check - healthy state"""
        # Mock connections with required ports
        mock_conn1 = Mock()
        mock_conn1.laddr.port = 3000
        mock_conn2 = Mock()
        mock_conn2.laddr.port = 8000
        mock_conn3 = Mock()
        mock_conn3.laddr.port = 8080
        
        mock_connections.return_value = [mock_conn1, mock_conn2, mock_conn3]
        
        check = monitor.health_checks["service_ports"]
        result = await monitor.check_service_ports(check)
        
        assert result.status == HealthStatus.HEALTHY
        assert "All 3 ports are active" in result.message
    
    @pytest.mark.asyncio
    @patch('psutil.process_iter')
    async def test_check_agent_processes_found(self, mock_process_iter, monitor):
        """Test agent processes check - agents found"""
        # Mock processes
        mock_proc1 = Mock()
        mock_proc1.info = {
            'pid': 1234,
            'name': 'python3',
            'cmdline': ['python3', '-m', 'agno', 'run']
        }
        mock_proc2 = Mock()
        mock_proc2.info = {
            'pid': 5678,
            'name': 'python3',
            'cmdline': ['python3', 'serena_server.py']
        }
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        check = monitor.health_checks["agent_processes"]
        result = await monitor.check_agent_processes(check)
        
        assert result.status == HealthStatus.HEALTHY
        assert "Found 2 agent processes" in result.message
        assert len(result.metrics["agent_processes"]) == 2
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_check_network_connectivity_success(self, mock_subprocess, monitor):
        """Test network connectivity check - success"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        check = monitor.health_checks["network_connectivity"]
        result = await monitor.check_network_connectivity(check)
        
        assert result.status == HealthStatus.HEALTHY
        assert "Network connectivity OK" in result.message
    
    @pytest.mark.asyncio
    @patch('psutil.disk_io_counters')
    async def test_check_storage_health_success(self, mock_disk_io, monitor):
        """Test storage health check - success"""
        mock_disk_io.return_value = Mock(
            read_count=1000,
            write_count=500,
            read_bytes=1048576,
            write_bytes=524288,
            read_time=100,
            write_time=50
        )
        
        check = monitor.health_checks["storage_health"]
        result = await monitor.check_storage_health(check)
        
        assert result.status == HealthStatus.HEALTHY
        assert "Storage health OK" in result.message
        assert result.metrics["read_count"] == 1000


class TestHealthCheckExecution:
    """Test health check execution and scheduling"""
    
    @pytest.fixture
    def monitor(self):
        return HealthMonitor()
    
    @pytest.mark.asyncio
    async def test_execute_health_check_success(self, monitor):
        """Test successful health check execution"""
        check = HealthCheck(
            name="Test Check",
            component_type=ComponentType.SYSTEM,
            description="Test check",
            check_function="check_cpu_usage",
            timeout_seconds=5
        )
        
        with patch.object(monitor, 'check_cpu_usage') as mock_check:
            mock_result = HealthResult(
                check_name="Test Check",
                status=HealthStatus.HEALTHY,
                message="Test passed",
                timestamp=datetime.now()
            )
            mock_check.return_value = mock_result
            
            result = await monitor._execute_health_check(check)
            
            assert result.check_name == "Test Check"
            assert result.status == HealthStatus.HEALTHY
            assert result.duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_execute_health_check_timeout(self, monitor):
        """Test health check execution timeout"""
        check = HealthCheck(
            name="Timeout Check",
            component_type=ComponentType.SYSTEM,
            description="Test timeout",
            check_function="check_cpu_usage",
            timeout_seconds=0.1
        )
        
        with patch.object(monitor, 'check_cpu_usage') as mock_check:
            # Make the check hang
            mock_check.side_effect = lambda x: asyncio.sleep(1)
            
            result = await monitor._execute_health_check(check)
            
            assert result.status == HealthStatus.CRITICAL
            assert "timed out" in result.message
            assert result.error == "Timeout"
    
    @pytest.mark.asyncio
    async def test_execute_health_check_exception(self, monitor):
        """Test health check execution with exception"""
        check = HealthCheck(
            name="Error Check",
            component_type=ComponentType.SYSTEM,
            description="Test error",
            check_function="check_cpu_usage",
            timeout_seconds=5
        )
        
        with patch.object(monitor, 'check_cpu_usage') as mock_check:
            mock_check.side_effect = Exception("Test error")
            
            result = await monitor._execute_health_check(check)
            
            assert result.status == HealthStatus.UNKNOWN
            assert "Test error" in result.message
            assert result.error == "Test error"


class TestSystemMetrics:
    """Test system metrics collection"""
    
    @pytest.fixture
    def monitor(self):
        return HealthMonitor()
    
    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.getloadavg')
    @patch('psutil.net_io_counters')
    @patch('psutil.disk_io_counters')
    @patch('psutil.pids')
    @patch('psutil.boot_time')
    @patch('time.time')
    async def test_collect_system_metrics(self, mock_time, mock_boot_time, 
                                        mock_pids, mock_disk_io, mock_net_io,
                                        mock_load, mock_disk, mock_memory, 
                                        mock_cpu, monitor):
        """Test system metrics collection"""
        # Mock all system calls
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(percent=60.2)
        mock_disk.return_value = Mock(used=500000000, total=1000000000)
        mock_load.return_value = (1.0, 1.2, 1.1)
        mock_net_io.return_value = Mock(
            bytes_sent=1000000,
            bytes_recv=2000000,
            packets_sent=1000,
            packets_recv=2000
        )
        mock_disk_io.return_value = Mock(
            read_bytes=1048576,
            write_bytes=524288,
            read_count=100,
            write_count=50
        )
        mock_pids.return_value = [1, 2, 3, 4, 5]
        mock_boot_time.return_value = 1000000000
        mock_time.return_value = 1000003600  # 1 hour uptime
        
        await monitor._collect_system_metrics()
        
        assert len(monitor.metrics_history) == 1
        metrics = monitor.metrics_history[0]
        
        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent == 25.5
        assert metrics.memory_percent == 60.2
        assert metrics.disk_percent == 50.0
        assert metrics.load_average == [1.0, 1.2, 1.1]
        assert metrics.process_count == 5
        assert metrics.uptime_seconds == 3600


class TestHealthSummary:
    """Test health summary generation"""
    
    @pytest.fixture
    def monitor(self):
        return HealthMonitor()
    
    @pytest.mark.asyncio
    async def test_get_health_summary_empty(self, monitor):
        """Test health summary with no results"""
        summary = await monitor.get_health_summary()
        
        assert summary["overall_status"] == HealthStatus.HEALTHY.value
        assert summary["checks"] == {}
        assert summary["alerts"] == []
        assert summary["stats"]["total_checks"] == 9
        assert summary["stats"]["critical_alerts"] == 0
        assert summary["stats"]["warning_alerts"] == 0
    
    @pytest.mark.asyncio
    async def test_get_health_summary_with_results(self, monitor):
        """Test health summary with health check results"""
        # Add some health results
        monitor.health_results["test_check_1"] = HealthResult(
            check_name="Test Check 1",
            status=HealthStatus.HEALTHY,
            message="All good",
            timestamp=datetime.now()
        )
        
        monitor.health_results["test_check_2"] = HealthResult(
            check_name="Test Check 2",
            status=HealthStatus.WARNING,
            message="Warning state",
            timestamp=datetime.now()
        )
        
        monitor.health_results["test_check_3"] = HealthResult(
            check_name="Test Check 3",
            status=HealthStatus.CRITICAL,
            message="Critical issue",
            timestamp=datetime.now()
        )
        
        summary = await monitor.get_health_summary()
        
        assert summary["overall_status"] == HealthStatus.CRITICAL.value
        assert len(summary["checks"]) == 3
        assert len(summary["alerts"]) == 2  # Warning + Critical
        assert summary["stats"]["critical_alerts"] == 1
        assert summary["stats"]["warning_alerts"] == 1
    
    @pytest.mark.asyncio
    async def test_get_health_summary_with_metrics(self, monitor):
        """Test health summary with system metrics"""
        # Add system metrics
        metrics = SystemMetrics(
            cpu_percent=25.0,
            memory_percent=60.0,
            disk_percent=45.0,
            load_average=[1.0, 1.2, 1.1],
            network_io={"bytes_sent": 1000, "bytes_recv": 2000},
            disk_io={"read_bytes": 1024, "write_bytes": 512},
            process_count=50,
            uptime_seconds=3600,
            timestamp=datetime.now()
        )
        monitor.metrics_history.append(metrics)
        
        summary = await monitor.get_health_summary()
        
        assert "metrics" in summary
        assert summary["metrics"]["cpu_percent"] == 25.0
        assert summary["metrics"]["memory_percent"] == 60.0
        assert summary["metrics"]["process_count"] == 50


class TestMetricsHistory:
    """Test metrics history management"""
    
    @pytest.fixture
    def monitor(self):
        return HealthMonitor()
    
    @pytest.mark.asyncio
    async def test_get_metrics_history_empty(self, monitor):
        """Test getting metrics history when empty"""
        history = await monitor.get_metrics_history(hours=1)
        
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_metrics_history_with_data(self, monitor):
        """Test getting metrics history with data"""
        # Add metrics from different times
        now = datetime.now()
        
        # Recent metric (within 1 hour)
        recent_metric = SystemMetrics(
            cpu_percent=25.0,
            memory_percent=60.0,
            disk_percent=45.0,
            load_average=[1.0, 1.2, 1.1],
            network_io={},
            disk_io={},
            process_count=50,
            uptime_seconds=3600,
            timestamp=now
        )
        
        # Old metric (2 hours ago)
        old_metric = SystemMetrics(
            cpu_percent=30.0,
            memory_percent=65.0,
            disk_percent=50.0,
            load_average=[1.5, 1.7, 1.6],
            network_io={},
            disk_io={},
            process_count=55,
            uptime_seconds=7200,
            timestamp=now - timedelta(hours=2)
        )
        
        monitor.metrics_history.extend([old_metric, recent_metric])
        
        # Get last 1 hour
        history = await monitor.get_metrics_history(hours=1)
        
        assert len(history) == 1
        assert history[0]["cpu_percent"] == 25.0
    
    def test_cleanup_old_data(self, monitor):
        """Test cleanup of old data"""
        # Add many metrics (more than limit)
        for i in range(1200):
            metric = SystemMetrics(
                cpu_percent=float(i),
                memory_percent=60.0,
                disk_percent=45.0,
                load_average=[1.0, 1.2, 1.1],
                network_io={},
                disk_io={},
                process_count=50,
                uptime_seconds=3600,
                timestamp=datetime.now()
            )
            monitor.metrics_history.append(metric)
        
        # Add old health result
        old_result = HealthResult(
            check_name="Old Check",
            status=HealthStatus.HEALTHY,
            message="Old result",
            timestamp=datetime.now() - timedelta(hours=25)
        )
        monitor.health_results["old_check"] = old_result
        
        # Add recent health result
        recent_result = HealthResult(
            check_name="Recent Check",
            status=HealthStatus.HEALTHY,
            message="Recent result",
            timestamp=datetime.now()
        )
        monitor.health_results["recent_check"] = recent_result
        
        monitor._cleanup_old_data()
        
        # Check metrics cleanup
        assert len(monitor.metrics_history) == 1000
        
        # Check health results cleanup
        assert "old_check" not in monitor.health_results
        assert "recent_check" in monitor.health_results


class TestHealthCheckManagement:
    """Test health check enable/disable functionality"""
    
    @pytest.fixture
    def monitor(self):
        return HealthMonitor()
    
    def test_enable_check(self, monitor):
        """Test enabling a health check"""
        monitor.health_checks["system_cpu"].enabled = False
        
        result = monitor.enable_check("system_cpu")
        
        assert result is True
        assert monitor.health_checks["system_cpu"].enabled is True
    
    def test_enable_nonexistent_check(self, monitor):
        """Test enabling non-existent health check"""
        result = monitor.enable_check("nonexistent_check")
        
        assert result is False
    
    def test_disable_check(self, monitor):
        """Test disabling a health check"""
        result = monitor.disable_check("system_cpu")
        
        assert result is True
        assert monitor.health_checks["system_cpu"].enabled is False
    
    def test_disable_nonexistent_check(self, monitor):
        """Test disabling non-existent health check"""
        result = monitor.disable_check("nonexistent_check")
        
        assert result is False


class TestDataClasses:
    """Test data class functionality"""
    
    def test_health_check_creation(self):
        """Test HealthCheck creation"""
        check = HealthCheck(
            name="Test Check",
            component_type=ComponentType.SYSTEM,
            description="Test description",
            check_function="test_function"
        )
        
        assert check.name == "Test Check"
        assert check.component_type == ComponentType.SYSTEM
        assert check.interval_seconds == 60  # Default
        assert check.enabled is True  # Default
        assert check.thresholds == {}  # Default
    
    def test_health_result_creation(self):
        """Test HealthResult creation"""
        timestamp = datetime.now()
        result = HealthResult(
            check_name="Test Check",
            status=HealthStatus.HEALTHY,
            message="All good",
            timestamp=timestamp
        )
        
        assert result.check_name == "Test Check"
        assert result.status == HealthStatus.HEALTHY
        assert result.timestamp == timestamp
        assert result.metrics == {}  # Default
        assert result.duration_ms == 0  # Default
    
    def test_system_metrics_creation(self):
        """Test SystemMetrics creation"""
        timestamp = datetime.now()
        metrics = SystemMetrics(
            cpu_percent=25.0,
            memory_percent=60.0,
            disk_percent=45.0,
            load_average=[1.0, 1.2, 1.1],
            network_io={"bytes_sent": 1000},
            disk_io={"read_bytes": 1024},
            process_count=50,
            uptime_seconds=3600,
            timestamp=timestamp
        )
        
        assert metrics.cpu_percent == 25.0
        assert metrics.process_count == 50
        assert metrics.timestamp == timestamp


@pytest.mark.integration
class TestHealthMonitorIntegration:
    """Integration tests for HealthMonitor with real system"""
    
    @pytest.fixture
    def real_monitor(self):
        """Create monitor for real system testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield HealthMonitor(config_dir=Path(temp_dir))
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--integration"),
        reason="Integration tests require --integration flag"
    )
    async def test_real_system_metrics_collection(self, real_monitor):
        """Test real system metrics collection"""
        await real_monitor._collect_system_metrics()
        
        assert len(real_monitor.metrics_history) == 1
        metrics = real_monitor.metrics_history[0]
        
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.disk_percent >= 0
        assert len(metrics.load_average) == 3
        assert metrics.process_count > 0
        assert metrics.uptime_seconds > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--integration"),
        reason="Integration tests require --integration flag"
    )
    async def test_real_health_checks_execution(self, real_monitor):
        """Test real health checks execution"""
        # Execute a few health checks
        cpu_check = real_monitor.health_checks["system_cpu"]
        cpu_result = await real_monitor.check_cpu_usage(cpu_check)
        
        memory_check = real_monitor.health_checks["system_memory"]
        memory_result = await real_monitor.check_memory_usage(memory_check)
        
        assert cpu_result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert memory_result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert cpu_result.duration_ms == 0  # Not set in direct call
        assert memory_result.duration_ms == 0


@pytest.mark.performance
class TestHealthMonitorPerformance:
    """Performance tests for HealthMonitor"""
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks_performance(self):
        """Test performance of concurrent health checks"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = HealthMonitor(config_dir=Path(temp_dir))
            
            start_time = time.time()
            
            # Execute multiple health checks concurrently
            tasks = []
            for check_name, check_config in list(monitor.health_checks.items())[:5]:
                if hasattr(monitor, check_config.check_function):
                    check_func = getattr(monitor, check_config.check_function)
                    tasks.append(check_func(check_config))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert len(results) == 5
            assert duration < 10.0  # Should complete reasonably quickly
            
            # Check that most operations succeeded
            successful_results = [r for r in results if isinstance(r, HealthResult)]
            assert len(successful_results) >= 3  # At least 3 should succeed


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=src.serena.monitoring.health_monitor",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])
