import time
import logging
from typing import Callable, Any, Optional
from enum import Enum
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""

    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation for resilience"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "circuit_breaker",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

        logger.info(
            f"Circuit breaker '{name}' initialized with threshold {failure_threshold}"
        )

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)

        return wrapper

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""

        # Check if circuit should be opened
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN, failing fast")
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")

        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - reset failure count
            self._on_success()
            return result

        except self.expected_exception as e:
            # Expected failure - increment failure count
            self._on_failure()
            logger.warning(f"Circuit breaker '{self.name}' failure: {e}")
            raise

        except Exception as e:
            # Unexpected failure - also count as failure
            self._on_failure()
            logger.error(f"Circuit breaker '{self.name}' unexpected failure: {e}")
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")

        self.failure_count = 0
        self.last_failure_time = None

    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker '{self.name}' transitioning to OPEN after {self.failure_count} failures"
                )

    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }

    def reset(self):
        """Manually reset the circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""

    def __init__(self):
        self.breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
                name=name,
            )

        return self.breakers[name]

    def get_all_states(self) -> dict:
        """Get states of all circuit breakers"""
        return {name: breaker.get_state() for name, breaker in self.breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()

    def reset_breaker(self, name: str):
        """Reset a specific circuit breaker"""
        if name in self.breakers:
            self.breakers[name].reset()


# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception,
):
    """Decorator for circuit breaker pattern"""

    def decorator(func: Callable) -> Callable:
        breaker = circuit_manager.get_breaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
        )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
