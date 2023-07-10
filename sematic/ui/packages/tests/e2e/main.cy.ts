describe("Sematic application", () => {
    it("renders the landing page", () => {
        cy.then(() => {
            window.localStorage.setItem("sematic-feature-flag-newui", "true");
        });
        cy.visit("/");
        cy.contains("Start your own project");
    });

    it("renders the pipeline index page", () => {
        cy.then(() => {
            window.localStorage.setItem("sematic-feature-flag-newui", "true");
        });
        cy.visit("/pipelines");

        const table = cy.getBySel("RunList");
        table.should("exist");

        table.within(() => {
            cy.getBySel("runlist-row").its("length").should("be.gte", 1);
        });
    });

    it("renders the run search page", () => {
        cy.then(() => {
            window.localStorage.setItem("sematic-feature-flag-newui", "true");
        });
        cy.visit("/runs");

        const table = cy.getBySel("RunList");
        table.should("exist");

        table.within(() => {
            cy.getBySel("runlist-row").its("length").should("be.gte", 1);
        });
    });

    it("renders the run details page", () => {
        cy.then(() => {
            window.localStorage.setItem("sematic-feature-flag-newui", "true");
        });
        cy.visit("/runs");

        cy.getBySel("runlist-row").first().click();

        cy.url().should("to.match", /\/runs\/[a-z0-9]+/);
    });
})
