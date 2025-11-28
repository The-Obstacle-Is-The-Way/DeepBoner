"""Unit tests for graph builder utilities."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic_ai import Agent

from src.agent_factory.graph_builder import (
    AgentNode,
    ConditionalEdge,
    DecisionNode,
    GraphBuilder,
    GraphNode,
    ParallelNode,
    ResearchGraph,
    SequentialEdge,
    StateNode,
    create_deep_graph,
    create_iterative_graph,
)
from src.middleware.state_machine import WorkflowState


class TestGraphNode:
    """Tests for GraphNode models."""

    def test_graph_node_creation(self):
        """Test creating a base GraphNode."""
        node = GraphNode(node_id="test_node", node_type="agent", description="Test")
        assert node.node_id == "test_node"
        assert node.node_type == "agent"
        assert node.description == "Test"

    def test_agent_node_creation(self):
        """Test creating an AgentNode."""
        mock_agent = MagicMock(spec=Agent)
        node = AgentNode(
            node_id="agent_1",
            agent=mock_agent,
            description="Test agent",
        )
        assert node.node_id == "agent_1"
        assert node.node_type == "agent"
        assert node.agent == mock_agent
        assert node.input_transformer is None
        assert node.output_transformer is None

    def test_agent_node_with_transformers(self):
        """Test creating an AgentNode with transformers."""
        mock_agent = MagicMock(spec=Agent)

        def input_transformer(x):
            return f"input_{x}"

        def output_transformer(x):
            return f"output_{x}"

        node = AgentNode(
            node_id="agent_1",
            agent=mock_agent,
            input_transformer=input_transformer,
            output_transformer=output_transformer,
        )
        assert node.input_transformer is not None
        assert node.output_transformer is not None

    def test_state_node_creation(self):
        """Test creating a StateNode."""

        def state_updater(state: WorkflowState, data: Any) -> WorkflowState:
            return state

        node = StateNode(
            node_id="state_1",
            state_updater=state_updater,
            description="Test state",
        )
        assert node.node_id == "state_1"
        assert node.node_type == "state"
        assert node.state_updater is not None
        assert node.state_reader is None

    def test_decision_node_creation(self):
        """Test creating a DecisionNode."""

        def decision_func(data: Any) -> str:
            return "next_node"

        node = DecisionNode(
            node_id="decision_1",
            decision_function=decision_func,
            options=["next_node", "other_node"],
            description="Test decision",
        )
        assert node.node_id == "decision_1"
        assert node.node_type == "decision"
        assert len(node.options) == 2
        assert "next_node" in node.options

    def test_parallel_node_creation(self):
        """Test creating a ParallelNode."""
        node = ParallelNode(
            node_id="parallel_1",
            parallel_nodes=["node1", "node2", "node3"],
            description="Test parallel",
        )
        assert node.node_id == "parallel_1"
        assert node.node_type == "parallel"
        assert len(node.parallel_nodes) == 3
        assert node.aggregator is None


class TestGraphEdge:
    """Tests for GraphEdge models."""

    def test_sequential_edge_creation(self):
        """Test creating a SequentialEdge."""
        edge = SequentialEdge(from_node="node1", to_node="node2")
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.condition is None
        assert edge.weight == 1.0

    def test_conditional_edge_creation(self):
        """Test creating a ConditionalEdge."""

        def condition(data: Any) -> bool:
            return True

        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition=condition,
            condition_description="Test condition",
        )
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.condition is not None
        assert edge.condition_description == "Test condition"


class TestResearchGraph:
    """Tests for ResearchGraph class."""

    def test_graph_creation(self):
        """Test creating an empty graph."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        assert graph.entry_node == "start"
        assert len(graph.exit_nodes) == 1
        assert graph.exit_nodes[0] == "end"
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        """Test adding a node to the graph."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        node = GraphNode(node_id="node1", node_type="agent", description="Test")
        graph.add_node(node)
        assert "node1" in graph.nodes
        assert graph.get_node("node1") == node

    def test_add_node_duplicate_raises_error(self):
        """Test that adding duplicate node raises ValueError."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        node = GraphNode(node_id="node1", node_type="agent", description="Test")
        graph.add_node(node)
        with pytest.raises(ValueError, match="already exists"):
            graph.add_node(node)

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        node1 = GraphNode(node_id="node1", node_type="agent", description="Test")
        node2 = GraphNode(node_id="node2", node_type="agent", description="Test")
        graph.add_node(node1)
        graph.add_node(node2)

        edge = SequentialEdge(from_node="node1", to_node="node2")
        graph.add_edge(edge)
        assert "node1" in graph.edges
        assert len(graph.edges["node1"]) == 1
        assert graph.edges["node1"][0] == edge

    def test_add_edge_invalid_source_raises_error(self):
        """Test that adding edge with invalid source raises ValueError."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        edge = SequentialEdge(from_node="nonexistent", to_node="node2")
        with pytest.raises(ValueError, match=r"Source node.*not found"):
            graph.add_edge(edge)

    def test_add_edge_invalid_target_raises_error(self):
        """Test that adding edge with invalid target raises ValueError."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        node1 = GraphNode(node_id="node1", node_type="agent", description="Test")
        graph.add_node(node1)
        edge = SequentialEdge(from_node="node1", to_node="nonexistent")
        with pytest.raises(ValueError, match=r"Target node.*not found"):
            graph.add_edge(edge)

    def test_get_next_nodes(self):
        """Test getting next nodes from a node."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        node1 = GraphNode(node_id="node1", node_type="agent", description="Test")
        node2 = GraphNode(node_id="node2", node_type="agent", description="Test")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(SequentialEdge(from_node="node1", to_node="node2"))

        next_nodes = graph.get_next_nodes("node1")
        assert len(next_nodes) == 1
        assert next_nodes[0][0] == "node2"

    def test_get_next_nodes_with_condition(self):
        """Test getting next nodes with conditional edge."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        node1 = GraphNode(node_id="node1", node_type="agent", description="Test")
        node2 = GraphNode(node_id="node2", node_type="agent", description="Test")
        node3 = GraphNode(node_id="node3", node_type="agent", description="Test")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # Add conditional edge that only passes when data is True
        def condition(data: Any) -> bool:
            return data is True

        graph.add_edge(SequentialEdge(from_node="node1", to_node="node2"))
        graph.add_edge(ConditionalEdge(from_node="node1", to_node="node3", condition=condition))

        # With condition True, should get both
        next_nodes = graph.get_next_nodes("node1", context=True)
        assert len(next_nodes) == 2

        # With condition False, should only get sequential edge
        next_nodes = graph.get_next_nodes("node1", context=False)
        assert len(next_nodes) == 1
        assert next_nodes[0][0] == "node2"

    def test_validate_empty_graph(self):
        """Test validating an empty graph."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        errors = graph.validate()
        assert len(errors) > 0  # Should have errors for missing entry/exit nodes

    def test_validate_valid_graph(self):
        """Test validating a valid graph."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        start_node = GraphNode(node_id="start", node_type="agent", description="Start")
        end_node = GraphNode(node_id="end", node_type="agent", description="End")
        graph.add_node(start_node)
        graph.add_node(end_node)
        graph.add_edge(SequentialEdge(from_node="start", to_node="end"))

        errors = graph.validate()
        assert len(errors) == 0

    def test_validate_unreachable_nodes(self):
        """Test that validation detects unreachable nodes."""
        graph = ResearchGraph(entry_node="start", exit_nodes=["end"])
        start_node = GraphNode(node_id="start", node_type="agent", description="Start")
        end_node = GraphNode(node_id="end", node_type="agent", description="End")
        unreachable = GraphNode(node_id="unreachable", node_type="agent", description="Unreachable")
        graph.add_node(start_node)
        graph.add_node(end_node)
        graph.add_node(unreachable)
        graph.add_edge(SequentialEdge(from_node="start", to_node="end"))

        errors = graph.validate_structure()
        assert len(errors) > 0
        assert any("unreachable" in error.lower() for error in errors)


class TestGraphBuilder:
    """Tests for GraphBuilder class."""

    def test_builder_initialization(self):
        """Test initializing a GraphBuilder."""
        builder = GraphBuilder()
        assert builder.graph is not None
        assert builder.graph.entry_node == ""
        assert len(builder.graph.exit_nodes) == 0

    def test_add_agent_node(self):
        """Test adding an agent node."""
        builder = GraphBuilder()
        mock_agent = MagicMock(spec=Agent)
        builder.add_agent_node("agent1", mock_agent, "Test agent")
        assert "agent1" in builder.graph.nodes
        node = builder.graph.get_node("agent1")
        assert isinstance(node, AgentNode)
        assert node.agent == mock_agent

    def test_add_state_node(self):
        """Test adding a state node."""
        builder = GraphBuilder()

        def updater(state: WorkflowState, data: Any) -> WorkflowState:
            return state

        builder.add_state_node("state1", updater, "Test state")
        assert "state1" in builder.graph.nodes
        node = builder.graph.get_node("state1")
        assert isinstance(node, StateNode)

    def test_add_decision_node(self):
        """Test adding a decision node."""
        builder = GraphBuilder()

        def decision_func(data: Any) -> str:
            return "next"

        builder.add_decision_node("decision1", decision_func, ["next", "other"], "Test")
        assert "decision1" in builder.graph.nodes
        node = builder.graph.get_node("decision1")
        assert isinstance(node, DecisionNode)

    def test_add_parallel_node(self):
        """Test adding a parallel node."""
        builder = GraphBuilder()
        builder.add_parallel_node("parallel1", ["node1", "node2"], "Test")
        assert "parallel1" in builder.graph.nodes
        node = builder.graph.get_node("parallel1")
        assert isinstance(node, ParallelNode)
        assert len(node.parallel_nodes) == 2

    def test_connect_nodes(self):
        """Test connecting nodes."""
        builder = GraphBuilder()
        builder.add_agent_node("node1", MagicMock(spec=Agent), "Node 1")
        builder.add_agent_node("node2", MagicMock(spec=Agent), "Node 2")
        builder.connect_nodes("node1", "node2")
        assert "node1" in builder.graph.edges
        assert len(builder.graph.edges["node1"]) == 1

    def test_connect_nodes_with_condition(self):
        """Test connecting nodes with a condition."""
        builder = GraphBuilder()
        builder.add_agent_node("node1", MagicMock(spec=Agent), "Node 1")
        builder.add_agent_node("node2", MagicMock(spec=Agent), "Node 2")

        def condition(data: Any) -> bool:
            return True

        builder.connect_nodes("node1", "node2", condition=condition, condition_description="Test")
        edge = builder.graph.edges["node1"][0]
        assert isinstance(edge, ConditionalEdge)
        assert edge.condition is not None

    def test_set_entry_node(self):
        """Test setting entry node."""
        builder = GraphBuilder()
        builder.add_agent_node("start", MagicMock(spec=Agent), "Start")
        builder.set_entry_node("start")
        assert builder.graph.entry_node == "start"

    def test_set_exit_nodes(self):
        """Test setting exit nodes."""
        builder = GraphBuilder()
        builder.add_agent_node("end1", MagicMock(spec=Agent), "End 1")
        builder.add_agent_node("end2", MagicMock(spec=Agent), "End 2")
        builder.set_exit_nodes(["end1", "end2"])
        assert len(builder.graph.exit_nodes) == 2

    def test_build_validates_graph(self):
        """Test that build() validates the graph."""
        builder = GraphBuilder()
        builder.add_agent_node("start", MagicMock(spec=Agent), "Start")
        builder.set_entry_node("start")
        # Missing exit node - should fail validation
        with pytest.raises(ValueError, match="validation failed"):
            builder.build()

    def test_build_returns_valid_graph(self):
        """Test that build() returns a valid graph."""
        builder = GraphBuilder()
        mock_agent = MagicMock(spec=Agent)
        builder.add_agent_node("start", mock_agent, "Start")
        builder.add_agent_node("end", mock_agent, "End")
        builder.connect_nodes("start", "end")
        builder.set_entry_node("start")
        builder.set_exit_nodes(["end"])

        graph = builder.build()
        assert isinstance(graph, ResearchGraph)
        assert graph.entry_node == "start"
        assert "end" in graph.exit_nodes


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_iterative_graph(self):
        """Test creating an iterative research graph."""
        mock_kg_agent = MagicMock(spec=Agent)
        mock_ts_agent = MagicMock(spec=Agent)
        mock_thinking_agent = MagicMock(spec=Agent)
        mock_writer_agent = MagicMock(spec=Agent)

        graph = create_iterative_graph(
            knowledge_gap_agent=mock_kg_agent,
            tool_selector_agent=mock_ts_agent,
            thinking_agent=mock_thinking_agent,
            writer_agent=mock_writer_agent,
        )

        assert isinstance(graph, ResearchGraph)
        assert graph.entry_node == "thinking"
        assert "writer" in graph.exit_nodes
        assert "thinking" in graph.nodes
        assert "knowledge_gap" in graph.nodes
        assert "continue_decision" in graph.nodes
        assert "tool_selector" in graph.nodes
        assert "writer" in graph.nodes

    def test_create_deep_graph(self):
        """Test creating a deep research graph."""
        mock_planner_agent = MagicMock(spec=Agent)
        mock_kg_agent = MagicMock(spec=Agent)
        mock_ts_agent = MagicMock(spec=Agent)
        mock_thinking_agent = MagicMock(spec=Agent)
        mock_writer_agent = MagicMock(spec=Agent)
        mock_long_writer_agent = MagicMock(spec=Agent)

        graph = create_deep_graph(
            planner_agent=mock_planner_agent,
            knowledge_gap_agent=mock_kg_agent,
            tool_selector_agent=mock_ts_agent,
            thinking_agent=mock_thinking_agent,
            writer_agent=mock_writer_agent,
            long_writer_agent=mock_long_writer_agent,
        )

        assert isinstance(graph, ResearchGraph)
        assert graph.entry_node == "planner"
        assert "synthesizer" in graph.exit_nodes
        assert "planner" in graph.nodes
        assert "parallel_loops_placeholder" in graph.nodes
        assert "synthesizer" in graph.nodes
