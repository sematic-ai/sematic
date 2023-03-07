import RunStateChip from "../RunStateChip";
import run from "ui-test/fixtures/run";

describe('RunStateChip component', () => {
    it("should render", () => {
        cy.mount(<RunStateChip run={run} />);
        cy.get("[data-cy-root]").matchImage({
            title: "RunStateChip component -- should render.green.snap"
        });

        let newRun = {...run, future_state: 'FAILED'};
        cy.mount(<RunStateChip run={newRun} />);
        cy.get("[data-cy-root]").matchImage({
            title: "RunStateChip component -- should render.red.snap"
        });
    });
});