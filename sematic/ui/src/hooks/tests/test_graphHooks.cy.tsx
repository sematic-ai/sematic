import { Graph, RunTreeNode } from "../../interfaces/graph";
import { useRunsTree } from "../graphHooks";
import { createRun } from "ui-test/support/utils"

describe('useRunsTree hook', () => {
    it("create a run tree from graph data", () => {
        const graph: Graph = {
            runs: [
                createRun({ id: "1", name: "run1", created_at: new Date("2021-01-01T00:00:00Z") }),
                createRun({ id: "4", name: "run4", created_at: new Date("2021-01-01T00:00:15Z") }),
                createRun({ id: "3", name: "run3", created_at: new Date("2021-01-01T00:00:10Z") }),
                createRun({ id: "2", name: "run2", created_at: new Date("2021-01-01T00:00:05Z") }),
                createRun({ id: "5", name: "run5", created_at: new Date("2021-01-01T00:01:05Z"), parent_id: "2" }),
                createRun({ id: "7", name: "run7", created_at: new Date("2021-01-01T00:01:25Z"), parent_id: "2" }),
                createRun({ id: "6", name: "run6", created_at: new Date("2021-01-01T00:01:15Z"), parent_id: "2" }),
                createRun({ id: "8", name: "run8", created_at: new Date("2021-01-01T00:02:00Z"), parent_id: "4" }),
            ],
            runsById: null as any,
            edges: null as any,
            artifacts: null as any,
            artifactsById: null as any,
        };

        let runTree: RunTreeNode | undefined

        const TestComponent = () => {
            runTree = useRunsTree(graph);
            return <></>;
        };

        cy.mount(<TestComponent />);
        cy.wait(0).then(() => {
            expect(runTree).to.eql({
                run: null,
                children: [
                    {
                        run: graph.runs[1],
                        children: [
                            {
                                run: graph.runs[7],
                                children: [],
                            },
                        ],
                    },
                    {
                        run: graph.runs[2],
                        children: [],
                    },
                    {
                        run: graph.runs[3],
                        children: [
                            {
                                run: graph.runs[5],
                                children: [],
                            },
                            {
                                run: graph.runs[6],
                                children: [],
                            },
                            {
                                run: graph.runs[4],
                                children: [],
                            },
                        ],
                    },
                    {
                        run: graph.runs[0],
                        children: [],
                    },
                ],
            });
        });
    });
});