import { Run } from "src/Models";
import RunsDropdown from "../RunsDropdown";

const mockData = [{
    id: "19595830c25e414cb943e1619e8d964c",
    created_at: "2023-04-25T16:29:17.985945+00:00",
    future_state: "RESOLVED"
},
{
    id: "297bafb56a124e27a8dec54850c6a9a2",
    created_at: "2023-05-25T16:29:17.985945+00:00",
    future_state: "CANCELED"
},
{
    id: "c7668586b35f480185768bc83c15d17d",
    created_at: "2022-06-25T16:29:17.985945+00:00",
    future_state: "RAN"
}] as unknown as Array<Run>;

describe("RunStateChip component", () => {
    it("should render", () => {
        cy.mount(<RunsDropdown runs={mockData} />);
        cy.get("[data-cy-root]").matchImage({
            title: "RunsDropdown component -- should render"
        });
    });
});
