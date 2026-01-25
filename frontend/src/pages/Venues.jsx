export default function Venues() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Venues</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Venue cards will be rendered here */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-2">Sample Venue</h2>
          <p className="text-gray-600">Location details</p>
        </div>
      </div>
    </div>
  )
}

