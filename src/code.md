```js
// Extracts product IDs to exclude from the .top-positioned container
function getExcludedProductIds() {
  const container = document.querySelector('.top-positioned');
  const scripts = container.querySelectorAll('script');
  let excludedIds = [];
  
  scripts.forEach(script => {
    const match = script.textContent.match(/productIds\.push\('(\d+)'\)/);
    if (match) {
      excludedIds.push(match[1]);
    }
  });
  
  return excludedIds;
}

// Filters an input array of product IDs, removing those found in the exclusion list
function filterProductIds(allProductIds) {
  const excludedIds = getExcludedProductIds();
  return allProductIds.filter(id => !excludedIds.includes(id));
}

// Generates a list of URL strings for the given product IDs, excluding any that are in the .top-positioned container
function generateProductLinks(allProductIds) {
  const filteredIds = filterProductIds(allProductIds);
  return filteredIds.map(id => `https://www.pazar3.mk/ad/${id}`);
}
// Navigate to a specific page number
function goToPage(pageNumber) {
  const baseUrl = "https://www.pazar3.mk/ads/vehicles/automobiles/vw-volkswagen/golf/golf/for-sale";
  const propParams = "36-37--from-year-2008,36-41--to-year-2012,,,,,";
  window.location.href = `${baseUrl}?Page=${pageNumber}&Prop=${propParams}`;
}

// Automatically go to the next page based on the current URL
function goToNextPage() {
  // Parse the current URL
  const url = new URL(window.location.href);
  // Get the current page from the URL query parameter; default to 1 if not set
  const currentPage = parseInt(url.searchParams.get('Page')) || 1;
  // Increment the page number
  url.searchParams.set('Page', currentPage + 1);
  // Navigate to the new URL
  window.location.href = url.toString();
}
function a() {
  // Parse the current URL
  const url = new URL(window.location.href);
  // Get the current page from the URL query parameter; default to 1 if not set
  const currentPage = parseInt(url.searchParams.get('Page')) || 1;
  // Increment the page number
  url.searchParams.set('Page', currentPage + 1);
  // Navigate to the new URL
  window.location.href = url.toString();
}

// Example usage:

const links = generateProductLinks(productIds);
console.log('Generated Links:', links);

goToNextPage();


```