import RunStateChip from "../RunStateChip";
import run from "@sematic/ui-test/fixtures/run";

describe('RunStateChip component', () => {
    it("should render", () => {
        cy.mount(<span data-snapshot-target><RunStateChip run={run} /></span>);
        cy.get("[data-snapshot-target]").matchImage({
            maxDiffThreshold: 0.1,
            title: "RunStateChip component -- should render.green.snap"
        });

        let newRun = {...run, future_state: 'FAILED'};
        cy.mount(<span data-snapshot-target><RunStateChip run={newRun} /></span>);
        cy.get("[data-snapshot-target]").matchImage({
            maxDiffThreshold: 0.1,
            title: "RunStateChip component -- should render.red.snap"
        });
    });
});