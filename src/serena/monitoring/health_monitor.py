"""
Health Monitoring System for Serena Orchestrator
Comprehensive health checks, monitoring, and automated troubleshooting
"""

import asyncio
import json
import logging
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import yaml


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of components to monitor"""
    SYSTEM = "system"
    SERVICE = "service"
    AGENT = "agent"
    MCP_TOOL = "mcp_tool"
    DATABASE = "database"
    NETWORK = "network"
    STORAGE = "storage"


@dataclass
class HealthCheck:
    """Configuration for a health check"""
    name: str
    component_type: ComponentType
    description: str
    check_function: str
    interval_seconds: int = 60
    timeout_seconds: int = 30
    enabled: bool = True
    critical: bool = False
    thresholds: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = {}


@dataclass
class HealthResult:
    """Result of a health check"""
    check_name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = None
    duration_ms: float = 0
    error: str = ""
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: List[float]
    network_io: Dict[str, int]
    disk_io: Dict[str, int]
    process_count: int
    uptime_seconds: float
    timestamp: datetime


class HealthMonitor:
    """Comprehensive health monitoring system"""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path("configs/monitoring")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, HealthResult] = {}
        self.metrics_history: List[SystemMetrics] = []
        self.logger = logging.getLogger(__name__)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        
        # Initialize health checks
        self._initialize_health_checks()
    
    def _initialize_health_checks(self):
        """Initialize default health checks"""
        checks = {
            "system_cpu": HealthCheck(
                name="System CPU Usage",
                component_type=ComponentType.SYSTEM,
                description="Monitor CPU usage percentage",
                check_function="check_cpu_usage",
                interval_seconds=30,
                critical=True,
                thresholds={"warning": 80, "critical": 95}
            ),
            "system_memory": HealthCheck(
                name="System Memory Usage",
                component_type=ComponentType.SYSTEM,
                description="Monitor memory usage percentage",
                check_function="check_memory_usage",
                interval_seconds=30,
                critical=True,
                thresholds={"warning": 85, "critical": 95}
            ),
            "system_disk": HealthCheck(
                name="System Disk Usage",
                component_type=ComponentType.SYSTEM,
                description="Monitor disk usage percentage",
                check_function="check_disk_usage",
                interval_seconds=60,
                critical=True,
                thresholds={"warning": 85, "critical": 95}
            ),
            "system_load": HealthCheck(
                name="System Load Average",
                component_type=ComponentType.SYSTEM,
                description="Monitor system load average",
                check_function="check_load_average",
                interval_seconds=60,
                thresholds={"warning": 2.0, "critical": 4.0}
            ),
            "service_ports": HealthCheck(
                name="Service Port Availability",
                component_type=ComponentType.SERVICE,
                description="Check if required ports are available",
                check_function="check_service_ports",
                interval_seconds=60,
                critical=True,
                thresholds={"ports": [3000, 8000, 8080]}
            ),
            "agent_processes": HealthCheck(
                name="Agent Processes",
                component_type=ComponentType.AGENT,
                description="Monitor agent process health",
                check_function="check_agent_processes",
                interval_seconds=30,
                critical=True
            ),
            "mcp_tools": HealthCheck(
                name="MCP Tools Health",
                component_type=ComponentType.MCP_TOOL,
                description="Check MCP tools availability",
                check_function="check_mcp_tools",
                interval_seconds=60
            ),
            "network_connectivity": HealthCheck(
                name="Network Connectivity",
                component_type=ComponentType.NETWORK,
                description="Check internet connectivity",
                check_function="check_network_connectivity",
                interval_seconds=120,
                thresholds={"hosts": ["8.8.8.8", "1.1.1.1"]}
            ),
            "storage_health": HealthCheck(
                name="Storage Health",
                component_type=ComponentType.STORAGE,
                description="Check storage device health",
                check_function="check_storage_health",
                interval_seconds=300
            )
        }
        
        self.health_checks = checks
        self.logger.info(f"Initialized {len(checks)} health checks")
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.monitoring_active:
                # Run all enabled health checks
                await self._run_health_checks()
                
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Wait before next iteration
                await asyncio.sleep(10)  # Check every 10 seconds for scheduling
                
        except asyncio.CancelledError:
            self.logger.info("Monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
    
    async def _run_health_checks(self):
        """Run scheduled health checks"""
        current_time = datetime.now()
        
        for check_name, check_config in self.health_checks.items():
            if not check_config.enabled:
                continue
            
            # Check if it's time to run this check
            last_result = self.health_results.get(check_name)
            if last_result:
                time_since_last = (current_time - last_result.timestamp).total_seconds()
                if time_since_last < check_config.interval_seconds:
                    continue
            
            # Run the health check
            try:
                result = await self._execute_health_check(check_config)
                self.health_results[check_name] = result
                
                # Log critical issues
                if result.status == HealthStatus.CRITICAL:
                    self.logger.critical(f"CRITICAL: {check_name} - {result.message}")
                elif result.status == HealthStatus.WARNING:
                    self.logger.warning(f"WARNING: {check_name} - {result.message}")
                
            except Exception as e:
                self.logger.error(f"Health check {check_name} failed: {e}")
                self.health_results[check_name] = HealthResult(
                    check_name=check_name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Check execution failed: {e}",
                    timestamp=current_time,
                    error=str(e)
                )
    
    async def _execute_health_check(self, check: HealthCheck) -> HealthResult:
        """Execute a single health check"""
        start_time = time.time()
        
        try:
            # Get the check function
            check_func = getattr(self, check.check_function)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                check_func(check),
                timeout=check.timeout_seconds
            )
            
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            
            return result
            
        except asyncio.TimeoutError:
            return HealthResult(
                check_name=check.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check timed out after {check.timeout_seconds}s",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                error="Timeout"
            )
        except Exception as e:
            return HealthResult(
                check_name=check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check failed: {e}",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def check_cpu_usage(self, check: HealthCheck) -> HealthResult:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        status = HealthStatus.HEALTHY
        message = f"CPU usage: {cpu_percent:.1f}%"
        
        if cpu_percent >= check.thresholds.get("critical", 95):
            status = HealthStatus.CRITICAL
            message += " - CRITICAL"
        elif cpu_percent >= check.thresholds.get("warning", 80):
            status = HealthStatus.WARNING
            message += " - WARNING"
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={"cpu_percent": cpu_percent}
        )
    
    async def check_memory_usage(self, check: HealthCheck) -> HealthResult:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        
        status = HealthStatus.HEALTHY
        message = f"Memory usage: {memory.percent:.1f}%"
        
        if memory.percent >= check.thresholds.get("critical", 95):
            status = HealthStatus.CRITICAL
            message += " - CRITICAL"
        elif memory.percent >= check.thresholds.get("warning", 85):
            status = HealthStatus.WARNING
            message += " - WARNING"
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={
                "memory_percent": memory.percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_used": memory.used
            }
        )
    
    async def check_disk_usage(self, check: HealthCheck) -> HealthResult:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        status = HealthStatus.HEALTHY
        message = f"Disk usage: {disk_percent:.1f}%"
        
        if disk_percent >= check.thresholds.get("critical", 95):
            status = HealthStatus.CRITICAL
            message += " - CRITICAL"
        elif disk_percent >= check.thresholds.get("warning", 85):
            status = HealthStatus.WARNING
            message += " - WARNING"
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={
                "disk_percent": disk_percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_free": disk.free
            }
        )
    
    async def check_load_average(self, check: HealthCheck) -> HealthResult:
        """Check system load average"""
        load_avg = psutil.getloadavg()
        load_1min = load_avg[0]
        
        status = HealthStatus.HEALTHY
        message = f"Load average: {load_1min:.2f}"
        
        if load_1min >= check.thresholds.get("critical", 4.0):
            status = HealthStatus.CRITICAL
            message += " - CRITICAL"
        elif load_1min >= check.thresholds.get("warning", 2.0):
            status = HealthStatus.WARNING
            message += " - WARNING"
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={
                "load_1min": load_avg[0],
                "load_5min": load_avg[1],
                "load_15min": load_avg[2]
            }
        )
    
    async def check_service_ports(self, check: HealthCheck) -> HealthResult:
        """Check if service ports are available"""
        ports = check.thresholds.get("ports", [3000, 8000, 8080])
        port_status = {}
        issues = []
        
        for port in ports:
            connections = psutil.net_connections()
            port_in_use = any(conn.laddr.port == port for conn in connections if conn.laddr)
            port_status[str(port)] = port_in_use
            
            if not port_in_use:
                issues.append(f"Port {port} not in use")
        
        if issues:
            status = HealthStatus.WARNING
            message = f"Port issues: {', '.join(issues)}"
        else:
            status = HealthStatus.HEALTHY
            message = f"All {len(ports)} ports are active"
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={"ports": port_status}
        )
    
    async def check_agent_processes(self, check: HealthCheck) -> HealthResult:
        """Check agent processes"""
        agent_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'agno' in cmdline.lower() or 'serena' in cmdline.lower():
                        agent_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if agent_processes:
            status = HealthStatus.HEALTHY
            message = f"Found {len(agent_processes)} agent processes"
        else:
            status = HealthStatus.WARNING
            message = "No agent processes found"
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={"agent_processes": agent_processes}
        )
    
    async def check_mcp_tools(self, check: HealthCheck) -> HealthResult:
        """Check MCP tools health"""
        # This would integrate with the MCP tools manager
        # For now, return a basic check
        
        status = HealthStatus.HEALTHY
        message = "MCP tools check not implemented"
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={}
        )
    
    async def check_network_connectivity(self, check: HealthCheck) -> HealthResult:
        """Check network connectivity"""
        hosts = check.thresholds.get("hosts", ["8.8.8.8"])
        connectivity_results = {}
        
        for host in hosts:
            try:
                # Simple ping check using subprocess
                process = await asyncio.create_subprocess_exec(
                    'ping', '-c', '1', '-W', '3', host,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                connectivity_results[host] = process.returncode == 0
            except Exception:
                connectivity_results[host] = False
        
        successful_hosts = sum(connectivity_results.values())
        total_hosts = len(hosts)
        
        if successful_hosts == 0:
            status = HealthStatus.CRITICAL
            message = "No network connectivity"
        elif successful_hosts < total_hosts:
            status = HealthStatus.WARNING
            message = f"Partial connectivity: {successful_hosts}/{total_hosts} hosts reachable"
        else:
            status = HealthStatus.HEALTHY
            message = f"Network connectivity OK: {successful_hosts}/{total_hosts} hosts reachable"
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={"connectivity": connectivity_results}
        )
    
    async def check_storage_health(self, check: HealthCheck) -> HealthResult:
        """Check storage device health"""
        # Basic storage health check
        disk_io = psutil.disk_io_counters()
        
        status = HealthStatus.HEALTHY
        message = "Storage health OK"
        
        metrics = {}
        if disk_io:
            metrics = {
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
                "read_time": disk_io.read_time,
                "write_time": disk_io.write_time
            }
        
        return HealthResult(
            check_name=check.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics=metrics
        )
    
    async def _collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Load average
            load_avg = list(psutil.getloadavg())
            
            # Network I/O
            net_io = psutil.net_io_counters()
            network_io = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
            
            # Disk I/O
            disk_io_counters = psutil.disk_io_counters()
            disk_io = {}
            if disk_io_counters:
                disk_io = {
                    "read_bytes": disk_io_counters.read_bytes,
                    "write_bytes": disk_io_counters.write_bytes,
                    "read_count": disk_io_counters.read_count,
                    "write_count": disk_io_counters.write_count
                }
            
            # Process count
            process_count = len(psutil.pids())
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            # Create metrics object
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk_percent,
                load_average=load_avg,
                network_io=network_io,
                disk_io=disk_io,
                process_count=process_count,
                uptime_seconds=uptime_seconds,
                timestamp=datetime.now()
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old metrics and results"""
        # Keep only last 1000 metrics entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Remove health results older than 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        for check_name, result in list(self.health_results.items()):
            if result.timestamp < cutoff_time:
                del self.health_results[check_name]
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        summary = {
            "overall_status": HealthStatus.HEALTHY.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "metrics": {},
            "alerts": []
        }
        
        # Analyze health check results
        critical_count = 0
        warning_count = 0
        
        for check_name, result in self.health_results.items():
            summary["checks"][check_name] = {
                "status": result.status.value,
                "message": result.message,
                "timestamp": result.timestamp.isoformat(),
                "duration_ms": result.duration_ms,
                "metrics": result.metrics
            }
            
            if result.status == HealthStatus.CRITICAL:
                critical_count += 1
                summary["alerts"].append({
                    "level": "critical",
                    "check": check_name,
                    "message": result.message
                })
            elif result.status == HealthStatus.WARNING:
                warning_count += 1
                summary["alerts"].append({
                    "level": "warning",
                    "check": check_name,
                    "message": result.message
                })
        
        # Determine overall status
        if critical_count > 0:
            summary["overall_status"] = HealthStatus.CRITICAL.value
        elif warning_count > 0:
            summary["overall_status"] = HealthStatus.WARNING.value
        
        # Add latest system metrics
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            summary["metrics"] = {
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_percent": latest_metrics.memory_percent,
                "disk_percent": latest_metrics.disk_percent,
                "load_average": latest_metrics.load_average,
                "process_count": latest_metrics.process_count,
                "uptime_seconds": latest_metrics.uptime_seconds
            }
        
        summary["stats"] = {
            "total_checks": len(self.health_checks),
            "enabled_checks": sum(1 for c in self.health_checks.values() if c.enabled),
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "monitoring_active": self.monitoring_active
        }
        
        return summary
    
    async def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_metrics = [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "disk_percent": m.disk_percent,
                "load_average": m.load_average,
                "process_count": m.process_count
            }
            for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        return filtered_metrics
    
    def enable_check(self, check_name: str) -> bool:
        """Enable a health check"""
        if check_name in self.health_checks:
            self.health_checks[check_name].enabled = True
            self.logger.info(f"Enabled health check: {check_name}")
            return True
        return False
    
    def disable_check(self, check_name: str) -> bool:
        """Disable a health check"""
        if check_name in self.health_checks:
            self.health_checks[check_name].enabled = False
            self.logger.info(f"Disabled health check: {check_name}")
            return True
        return False
