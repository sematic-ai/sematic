import RunsDropdown from "../RunsDropdown";

describe('RunStateChip component', () => {
    it("should render", () => {
        cy.mount(<RunsDropdown />);
        cy.get("[data-cy-root]").matchImage({
            title: "RunsDropdown component -- should render"
        });
    });
});