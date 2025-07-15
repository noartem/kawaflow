from unittest.mock import MagicMock, mock_open, patch

from kawa.core import Actor, ActorDefinition, Context, Event, EventDefinition
from kawa.module import Module
from kawa.utils import get_actor_uuid


def test_module_init_and_load():
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        with patch("builtins.open", new_callable=mock_open) as mock_builtin_open:
            mock_module_content = MagicMock()

            class MockEvent(Event):
                """Mock Event Docstring"""

                pass

            @Actor(receivs=(MockEvent,), sends=())
            def MockActor(ctx: Context, event: MockEvent):
                """Mock Actor Docstring"""
                pass

            mock_module_content.MockActor = MockActor
            mock_module_content.MockEvent = MockEvent
            mock_import_from_path.return_value = mock_module_content
            mock_builtin_open.return_value.read.return_value = (
                ""  # Ensure open is mocked for init
            )

            module = Module("dummy_path.py")

            assert get_actor_uuid(MockActor.funcOrClass) in module.actors
            assert EventDefinition.fromEventClass(MockEvent).id in module.events
            assert isinstance(
                module.actors[get_actor_uuid(MockActor.funcOrClass)], ActorDefinition
            )
            assert isinstance(
                module.events[EventDefinition.fromEventClass(MockEvent).id],
                EventDefinition,
            )


def test_module_init_no_actors_events():
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        with patch("builtins.open", new_callable=mock_open) as mock_builtin_open:
            mock_module_content = MagicMock()
            mock_import_from_path.return_value = mock_module_content
            mock_builtin_open.return_value.read.return_value = (
                ""  # Ensure open is mocked for init
            )

            module = Module("dummy_path.py")
            assert not module.actors
            assert not module.events


def test_module_init_multiple_actors_events():
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        with patch("builtins.open", new_callable=mock_open) as mock_builtin_open:
            mock_module_content = MagicMock()

            class MockEvent1(Event):
                pass

            class MockEvent2(Event):
                pass

            @Actor(receivs=(MockEvent1,), sends=())
            def MockActor1(ctx: Context, event: MockEvent1):
                pass

            @Actor(receivs=(MockEvent2,), sends=())
            def MockActor2(ctx: Context, event: MockEvent2):
                pass

            mock_module_content.MockActor1 = MockActor1
            mock_module_content.MockActor2 = MockActor2
            mock_module_content.MockEvent1 = MockEvent1
            mock_module_content.MockEvent2 = MockEvent2
            mock_import_from_path.return_value = mock_module_content
            mock_builtin_open.return_value.read.return_value = ""

            module = Module("dummy_path.py")
            assert get_actor_uuid(MockActor1.funcOrClass) in module.actors
            assert get_actor_uuid(MockActor2.funcOrClass) in module.actors
            assert EventDefinition.fromEventClass(MockEvent1).id in module.events
            assert EventDefinition.fromEventClass(MockEvent2).id in module.events
            assert len(module.actors) == 2
            assert len(module.events) == 2


@patch("kawa.module.Module._load")
def test_module_load_commands(mock_load):
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        file_content = "#! command1\nline2\n#! command2"
        with patch("builtins.open", new_callable=mock_open, read_data=file_content):
            mock_import_from_path.return_value = MagicMock()

            module = Module("dummy_path.py")
            module._load_commands()

            assert "command1" in module.commands
            assert "command2" in module.commands


@patch("kawa.module.Module._load")
def test_module_load_commands_no_commands(mock_load):
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        file_content = "line1\nline2\nline3"
        with patch("builtins.open", new_callable=mock_open, read_data=file_content):
            mock_import_from_path.return_value = MagicMock()

            module = Module("dummy_path.py")
            module._load_commands()
            assert not module.commands


@patch("kawa.module.Module._load")
def test_module_load_commands_malformed_commands(mock_load):
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        file_content = "#! command1\n#!   command2\n# ! not a command"
        with patch("builtins.open", new_callable=mock_open, read_data=file_content):
            mock_import_from_path.return_value = MagicMock()

            module = Module("dummy_path.py")
            module._load_commands()
            assert "command1" in module.commands
            assert "command2" in module.commands
            assert "not a command" not in module.commands
            assert len(module.commands) == 2


def test_module_dump():
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        with patch("builtins.open", new_callable=mock_open):
            mock_module_content = MagicMock()

            class MockEvent(Event):
                """Mock Event Docstring"""

                pass

            @Actor(receivs=(MockEvent,), sends=())
            def MockActor(ctx: Context, event: MockEvent):
                """Mock Actor Docstring"""
                pass

            mock_module_content.MockActor = MockActor
            mock_module_content.MockEvent = MockEvent
            mock_import_from_path.return_value = mock_module_content

            module = Module("dummy_path.py")
            dump_data = module.dump()

            assert "events" in dump_data
            assert "actors" in dump_data
            assert len(dump_data["events"]) > 0
            assert len(dump_data["actors"]) > 0

            event_ids = [e["id"] for e in dump_data["events"]]
            actor_ids = [a["id"] for a in dump_data["actors"]]

            assert EventDefinition.fromEventClass(MockEvent).id in event_ids
            assert get_actor_uuid(MockActor.funcOrClass) in actor_ids


def test_module_dump_no_actors_events():
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        with patch("builtins.open", new_callable=mock_open) as mock_builtin_open:
            mock_module_content = MagicMock()
            mock_import_from_path.return_value = mock_module_content
            mock_builtin_open.return_value.read.return_value = ""

            module = Module("dummy_path.py")
            dump_data = module.dump()

            assert "events" in dump_data
            assert "actors" in dump_data
            assert not dump_data["events"]
            assert not dump_data["actors"]


def test_module_dump_multiple_actors_events():
    with patch("kawa.module.import_from_path") as mock_import_from_path:
        with patch("builtins.open", new_callable=mock_open) as mock_builtin_open:
            mock_module_content = MagicMock()

            class MockEvent1(Event):
                pass

            class MockEvent2(Event):
                pass

            @Actor(receivs=(MockEvent1,), sends=())
            def MockActor1(ctx: Context, event: MockEvent1):
                pass

            @Actor(receivs=(MockEvent2,), sends=())
            def MockActor2(ctx: Context, event: MockEvent2):
                pass

            mock_module_content.MockActor1 = MockActor1
            mock_module_content.MockActor2 = MockActor2
            mock_module_content.MockEvent1 = MockEvent1
            mock_module_content.MockEvent2 = MockEvent2
            mock_import_from_path.return_value = mock_module_content
            mock_builtin_open.return_value.read.return_value = ""

            module = Module("dummy_path.py")
            dump_data = module.dump()

            assert len(dump_data["events"]) == 2
            assert len(dump_data["actors"]) == 2

            event_ids = [e["id"] for e in dump_data["events"]]
            actor_ids = [a["id"] for a in dump_data["actors"]]

            assert EventDefinition.fromEventClass(MockEvent1).id in event_ids
            assert EventDefinition.fromEventClass(MockEvent2).id in event_ids
            assert get_actor_uuid(MockActor1.funcOrClass) in actor_ids
            assert get_actor_uuid(MockActor2.funcOrClass) in actor_ids
