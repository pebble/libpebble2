from __future__ import absolute_import
__author__ = 'katharine'

from six import with_metaclass

from abc import ABCMeta, abstractmethod


class BaseEventHandler(with_metaclass(ABCMeta)):
    """
    An event handler, used throughout libpebble2 to indicate that something happened. These should ordinarily not need
    to be directly invoked by a client of libpebble2.
    """
    @abstractmethod
    def register_handler(self, event, handler):
        """
        Register a handler for an event.

        :param event: The event to be handled. This can be any object, as long as it's hashable.
        :param handler: A callback function to be called when the event is triggered. The arguments are dependent
                        on the event.
        :return: A handle that can be passed to :meth:`unregister_handler` to remove the registration.
        """
        pass

    @abstractmethod
    def unregister_handler(self, handle):
        """
        Remove a handler for an event using a handle returned by :meth:`register_handler`.

        :param handle: The handle for the registration to remove.
        """
        pass

    @abstractmethod
    def wait_for_event(self, event, timeout=10):
        """
        A blocking wait for an event to be fired.

        :param event: The event to wait on.
        :param timeout: How long to wait before raising :exc:`.TimeoutError`
        :return: The arguments that were passed to :meth:`broadcast_event`.
        """
        pass

    @abstractmethod
    def queue_events(self, event):
        """
        Returns a :class:`BaseEventQueue` from which events can be read as they arrive, even if the arrive faster
        than they are removed.

        :param event: The events to add to the queue.
        :return: An event queue.
        :rtype: BaseEventQueue
        """
        pass

    @abstractmethod
    def broadcast_event(self, event, *args):
        """
        Broadcasts an event to all subscribers for that event, as added by :meth:`register_handler`
        :meth:`wait_for_event` and :meth:`queue_events`. All arguments after `event` are passed on to the listeners.

        :param event: The event to broadcast.
        :param args: Any arguments to pass on.
        """
        pass


class BaseEventQueue(with_metaclass(ABCMeta)):
    @abstractmethod
    def close(self):
        """
        Stop adding events to this queue. It is illegal to call :meth:`get` or iterate over this queue after calling
        :meth:`close`.
        """
        pass

    @abstractmethod
    def get(self, timeout=10):
        """
        Get the next event in the queue. Blocks until an item is available.
        """
        pass

    @abstractmethod
    def __iter__(self):
        """
        Iterate over events in the queue. Blocks if no more items are available.
        """
        pass


