describe("Sematic application", () => {
  it("renders the pipeline index page", () => {
    cy.visit("/");
    cy.contains("Welcome to Sematic");

    cy.visit("/pipelines");

    const table = cy.getBySel("RunList");
    table.should("exist");

    table.within(() => {
      cy.getBySel("runlist-row").its("length").should("be.gte", 1);
    });
  })
})
