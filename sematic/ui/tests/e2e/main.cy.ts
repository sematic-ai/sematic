describe('Sematic application', () => {
  it('renders the pipeline index page', () => {
    cy.visit('http://127.0.0.1:5001/');
    cy.contains('Welcome to Sematic');

    cy.visit('http://127.0.0.1:5001/pipelines');

    const table = cy.getBySel('RunList');
    table.should('exist');

    table.within(() => {
      cy.getBySel('pipeline-row').its('length').should('be.greaterThan', 1);
    });
  })
})
